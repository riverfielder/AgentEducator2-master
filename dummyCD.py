import subprocess
import time
import sys
import os
import shutil

def get_current_commit():
    """获取当前HEAD的commit hash"""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"获取当前commit失败: {str(e)}")
    return None

def get_remote_commit():
    """获取远程HEAD的commit hash"""
    try:
        result = subprocess.run(['git', 'rev-parse', 'origin/HEAD'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"获取远程commit失败: {str(e)}")
    return None

def auto_deploy():
    target_dir = "/opt/1panel/www/sites/edu.homeworkkun.top/index"
    
    while True:
        try:
            # 执行git fetch
            #print(f"[{time.ctime()}] 执行 git fetch...")
            fetch_result = subprocess.run(['git', 'fetch'], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE,
                                        text=True)
            
            if fetch_result.returncode != 0:
                print(f"git fetch 失败: {fetch_result.stderr}")
                time.sleep(2)
                continue
                
            # 检查是否有变化
            current_commit = get_current_commit()
            remote_commit = get_remote_commit()
            
            if current_commit and remote_commit and current_commit != remote_commit:
                print(f"[{time.ctime()}] 检测到远程更新，开始部署...")
                

                pull_result = subprocess.run(['git', 'pull'], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE,
                                           text=True)
                
                if pull_result.returncode != 0:
                    print(f"git pull 失败: {pull_result.stderr}")
                    time.sleep(2)
                    continue
                    
                print("git pull 成功")
                
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
                        time.sleep(2)
                        continue
                        
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
                                shutil.copytree(src_path, dst_path,dirs_exist_ok=True)
                            else:
                                shutil.copy2(src_path, dst_path)
                        
                        print("静态资源拷贝完成")
                        print("部署完成！")
                    else:
                        print(f"构建目录 {dist_dir} 不存在")
                else:
                    print(f"frontend目录 {frontend_dir} 不存在")
            else:
                pass
            
        except Exception as e:
            print(f"[{time.ctime()}] 发生异常: {str(e)}")
        
        # 等待2秒
        time.sleep(2)

if __name__ == "__main__":
    print("开始自动部署监控，每2秒检查一次远程更新... (按Ctrl+C停止)")
    try:
        auto_deploy()
    except KeyboardInterrupt:
        print("\n停止自动部署监控")
        sys.exit(0)