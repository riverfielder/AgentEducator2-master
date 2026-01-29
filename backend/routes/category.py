from flask import Blueprint, jsonify
from models.models import Course, db
import json

category_bp = Blueprint('category', __name__)

@category_bp.route('/list', methods=['GET'])
def list_categories():
    """
    获取所有课程的分类列表
    直接从数据库中查询所有课程的描述字段，并从中提取分类信息
    """
    try:
        courses_with_desc = db.session.query(Course.description).filter(
            Course.is_deleted == False, 
            Course.description.isnot(None),
            Course.description != ''
        ).all()

        category_set = set()
        for course_desc_tuple in courses_with_desc:
            desc_str = course_desc_tuple[0]
            try:
                desc_json = json.loads(desc_str)
                categories = desc_json.get('category', [])
                if isinstance(categories, list):
                    for cat in categories:
                        if cat and isinstance(cat, str):
                            category_set.add(cat)
            except (json.JSONDecodeError, TypeError):
                continue
        
        return jsonify(sorted(list(category_set)))

    except Exception as e:
        print(f"Error fetching categories: {e}")
        return jsonify({"error": "Failed to retrieve categories"}), 500 