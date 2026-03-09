import os

file_path = r"backend/config/unified_llm_config.py"
new_model = "doubao-seed-1-8-251228"
old_models = ["doubao-seed-1-6-250615", "doubao-seed-1-6-flash-250615"]

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated_content = content
    count = 0
    for old in old_models:
        matches = updated_content.count(old)
        if matches > 0:
            updated_content = updated_content.replace(old, new_model)
            count += matches
            print(f"Replaced {matches} occurrences of {old}")
    
    if count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Successfully updated {file_path}. Total replacements: {count}")
    else:
        print("No matches found.")
else:
    print(f"File not found: {file_path}")
