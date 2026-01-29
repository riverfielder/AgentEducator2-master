from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
import json
import os
# 设置环境变量以解决 OpenMP 冲突
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import time
import uuid
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.memory import ConversationBufferMemory
from queue import Queue
from threading import Thread

app = Flask(__name__)
CORS(app)  # 支持跨域请求

# 配置信息
SILICON_API_BASE = "https://api.siliconflow.cn/v1"
API_KEY = "sk-gplnfadmdaipjskyauqadvqcgbbatvmcrguzcdbnmffsjrzt"  
VIDEO_DATA_PATH = "playground/keyframes_output/cc1147e9c64d5380a5f5ea9062513731-ld.json"
INDEX_SAVE_PATH = "playground/vector_index"

# 用于存储活跃对话的会话字典
active_sessions = {}

class StreamingCallback:
    """自定义回调处理流式输出"""
    def __init__(self, queue):
        self.queue = queue

    def on_llm_new_token(self, token, **kwargs):
        """当LLM生成新token时被调用"""
        self.queue.put(token)

def load_video_data(file_path):
    """加载视频数据"""
    video_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                video_data.append(json.loads(line))
    return video_data

def build_index(video_data, embeddings):
    """构建向量索引"""
    docs = []
    metadatas = []
    for video in video_data:
        video_name = video["video_name"]
        for keyframe in video.get("keyframes", []):
            ocr_text = " ".join(keyframe.get("ocr_result", []))
            asr_text = keyframe.get("asr_texts", "")
            content = f"屏幕内容：{ocr_text} 教师讲授： {asr_text}"
            docs.append(content)
            metadatas.append({
                "video_name": video_name,
                "time_point": keyframe["time_point"],
                "source": f"{video_name}@{keyframe['time_point']}"
            })
    
    # 构建索引
    index = FAISS.from_texts(docs, embeddings, metadatas=metadatas)
    
    # 保存索引以便后续复用
    if not os.path.exists(INDEX_SAVE_PATH):
        os.makedirs(INDEX_SAVE_PATH)
    index.save_local(INDEX_SAVE_PATH)
    
    return index

def get_or_create_index():
    """获取或创建向量索引"""
    embeddings = OpenAIEmbeddings(
        openai_api_key=API_KEY,
        base_url=SILICON_API_BASE,
        model='Pro/BAAI/bge-m3'
    )
    
    # 检查是否已有索引
    if os.path.exists(INDEX_SAVE_PATH):
        try:
            print(INDEX_SAVE_PATH, "索引已存在，正在加载...")
            index = FAISS.load_local(INDEX_SAVE_PATH, embeddings)
            return index
        except Exception as e:
            print(f"加载索引失败: {e}，正在重新构建...")
    
    # 构建新索引
    video_data = load_video_data(VIDEO_DATA_PATH)
    return build_index(video_data, embeddings)

def get_qa_chain(session_id=None, streaming_callback=None):
    """创建问答链，支持流式输出"""
    # 初始化LLM
    llm = ChatOpenAI(
        openai_api_key=API_KEY,
        openai_api_base=SILICON_API_BASE,
        temperature=0.7,
        model="deepseek-ai/DeepSeek-V3",
        streaming=streaming_callback is not None,
        callbacks=[streaming_callback] if streaming_callback else None
    )
    
    # 获取向量索引
    index = get_or_create_index()
    
    # 使用会话内存
    memory = None
    if session_id and session_id in active_sessions:
        memory = active_sessions[session_id]["memory"]
    else:
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        if session_id:
            active_sessions[session_id] = {"memory": memory, "last_active": time.time()}
    
    # 创建问答链
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=index.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        return_source_documents=True,
        chain_type="stuff"
    )
    
    return qa_chain



@app.route('/api/chat', methods=['POST', 'GET'])
def chat():
    """处理对话请求，支持普通和流式响应"""
    # 处理GET请求(用于SSE流式请求)
    if request.method == 'GET':
        query = request.args.get('query')
        session_id = request.args.get('session_id')
        stream = True  # GET请求默认使用流式响应
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    # 为新会话创建ID
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # 流式响应
    if stream:
        def generate():
            # 创建消息队列
            queue = Queue()
            callback = StreamingCallback(queue)
            
            # 在后台线程处理查询
            def process_query():
                qa_chain = get_qa_chain(session_id, callback)
                result = qa_chain({"query": query})
                # 添加文档来源信息
                sources = []
                if "source_documents" in result:
                    for doc in result["source_documents"]:
                        if hasattr(doc, "metadata"):
                            sources.append(doc.metadata)
                # 发送结束标记和源信息
                queue.put("[END]")
                queue.put(json.dumps({"sources": sources}))
            
            # 启动后台处理
            Thread(target=process_query).start()
            
            # 流式传输tokens
            while True:
                token = queue.get()
                if token == "[END]":
                    # 获取源信息
                    sources_json = queue.get()
                    yield f"data: {sources_json}\n\n"
                    break
                yield f"data: {token}\n\n"
        
        return Response(stream_with_context(generate()), 
                        content_type='text/event-stream')
    
    # 常规响应
    else:
        qa_chain = get_qa_chain(session_id)
        result = qa_chain({"query": query})
        
        answer = result.get("answer", "")
        sources = []
        
        if "source_documents" in result:
            for doc in result["source_documents"]:
                if hasattr(doc, "metadata"):
                    sources.append(doc.metadata)
        
        return jsonify({
            "answer": answer,
            "sources": sources,
            "session_id": session_id
        })

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return jsonify({"status": "success"})
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/upload', methods=['POST'])
def upload_video_data():
    """上传并处理新的视频数据文件"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # 保存上传的文件
    filename = f"upload_{int(time.time())}.json"
    filepath = os.path.join("playground/uploaded_data", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)
    
    # 重建索引
    try:
        embeddings = OpenAIEmbeddings(
            openai_api_key=API_KEY,
            base_url=SILICON_API_BASE,
            model='Pro/BAAI/bge-m3'
        )
        video_data = load_video_data(filepath)
        index = build_index(video_data, embeddings)
        return jsonify({"status": "success", "message": "索引构建完成"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 确保目录存在
    os.makedirs("playground/uploaded_data", exist_ok=True)
    # 启动时预加载索引
    get_or_create_index()
    app.run(host='0.0.0.0', port=5000, debug=True)