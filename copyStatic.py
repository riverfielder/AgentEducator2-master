import subprocess
import os
import shutil

def build_and_copy():
    """单次构建并拷贝静态资源"""
    target_dir = "/opt/1panel/www/sites/edu.homeworkkun.top/index"
    
    try:
        # 切换到frontend目录执行npm run build
        frontend_dir = os.path.join(os.getcwd(), 'frontend')
        if os.path.exists(frontend_dir):
            print("执行 npm run build...")
            build_result = subprocess.run(['npm', 'run', 'build'], 
                                        cwd=frontend_dir,
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE,
                                        text=True)
            
            if build_result.returncode != 0:
                print(f"npm run build 失败: {build_result.stderr}")
                return False
                
            print("npm run build 成功")
            
            # 拷贝静态资源
            dist_dir = os.path.join(frontend_dir, 'dist')
            if os.path.exists(dist_dir):
                print(f"拷贝静态资源到 {target_dir}...")
                
                # 确保目标目录存在
                os.makedirs(target_dir, exist_ok=True)
                
                # 拷贝新文件
                for item in os.listdir(dist_dir):
                    src_path = os.path.join(dist_dir, item)
                    dst_path = os.path.join(target_dir, item)
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src_path, dst_path)
                
                print("静态资源拷贝完成")
                print("部署完成！")
                return True
            else:
                print(f"构建目录 {dist_dir} 不存在")
                return False
        else:
            print(f"frontend目录 {frontend_dir} 不存在")
            return False
            
    except Exception as e:
        print(f"发生异常: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始构建并拷贝静态资源...")
    success = build_and_copy()
    if success:
        print("操作成功完成")
    else:
        print("操作失败")