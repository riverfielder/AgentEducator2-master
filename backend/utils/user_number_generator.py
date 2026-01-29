#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户编号生成工具
为新注册用户生成学号/教职工号
"""

import hashlib
import uuid
from datetime import datetime

def uuid_to_number(uuid_str, length=5):
    """
    将UUID转换为指定长度的数字串
    使用hash算法确保唯一性和一致性
    
    Args:
        uuid_str: UUID字符串
        length: 生成数字串的长度
    
    Returns:
        str: 指定长度的数字串
    """
    # 移除UUID中的连字符
    clean_uuid = uuid_str.replace('-', '')
    
    # 使用SHA256哈希
    hash_obj = hashlib.sha256(clean_uuid.encode())
    hash_hex = hash_obj.hexdigest()
    
    # 转换为数字（取前length位）
    number_str = ''
    for char in hash_hex:
        if char.isdigit():
            number_str += char
        else:
            # 将字母转换为数字 (a=1, b=2, ..., f=6)
            if char in 'abcdef':
                number_str += str(ord(char) - ord('a') + 1)
    
    # 取前length位，不足则补0
    result = number_str[:length].ljust(length, '0')
    return result

def generate_user_number(user_id, role):
    """
    根据用户ID和角色生成用户编号
    格式：S2025XXXXX (学生) 或 T2025XXXXX (教师)
    
    Args:
        user_id: 用户UUID
        role: 用户角色 ('student' 或 'teacher')
    
    Returns:
        str: 10位用户编号
    """
    # 角色前缀
    prefix = 'S' if role == 'student' else 'T'
    
    # 年份
    year = '2025'
    
    # 从UUID生成5位数字
    number_part = uuid_to_number(user_id, 5)
    
    return f"{prefix}{year}{number_part}"

def generate_unique_user_number(user_id, role, existing_numbers=None):
    """
    生成唯一的用户编号，避免重复
    
    Args:
        user_id: 用户UUID
        role: 用户角色
        existing_numbers: 已存在的编号集合（可选）
    
    Returns:
        str: 唯一的10位用户编号
    """
    if existing_numbers is None:
        existing_numbers = set()
    
    # 生成基础编号
    user_number = generate_user_number(user_id, role)
    
    # 检查重复，如果重复则重新生成
    counter = 0
    original_number = user_number
    while user_number in existing_numbers:
        counter += 1
        # 修改最后一位数字来避免重复
        last_digit = str((int(user_number[-1]) + counter) % 10)
        user_number = user_number[:-1] + last_digit
        
        # 如果修改超过10次，使用时间戳
        if counter > 10:
            timestamp = str(int(datetime.now().timestamp()))[-5:]
            user_number = original_number[:-5] + timestamp
            break
    
    return user_number

# 测试函数
if __name__ == "__main__":
    # 测试UUID转数字
    test_uuid = "123e4567-e89b-12d3-a456-426614174000"
    print(f"UUID: {test_uuid}")
    print(f"转换后: {uuid_to_number(test_uuid, 5)}")
    
    # 测试生成用户编号
    student_number = generate_user_number(test_uuid, 'student')
    teacher_number = generate_user_number(test_uuid, 'teacher')
    print(f"学生编号: {student_number}")
    print(f"教师编号: {teacher_number}")
    
    # 测试唯一性
    existing = {student_number}
    unique_number = generate_unique_user_number(test_uuid, 'student', existing)
    print(f"唯一编号: {unique_number}") 