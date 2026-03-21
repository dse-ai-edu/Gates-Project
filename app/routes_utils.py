import json 

def load_default_keywords(grouped_keywords):
    subgroup_identifier_list = [int(identifier) for identifier in grouped_keywords.keys()]
    subgroup_identifier_list = sorted(subgroup_identifier_list)
    result = [grouped_keywords[subgroup_identifier][0]["key"] for subgroup_identifier in subgroup_identifier_list]
    return result

def return_keyword_combination_example(keywords_str, default_keywords, example_path):
    with open(example_path, "r", encoding="utf-8") as f:
        example_data = json.load(f)
        
    keywords_str = keywords_str.strip("+")
    custom_keywords = keywords_str.split("+")
    default_keywords_str = "+".join(default_keywords)
    keywords_list = []
    for custom_kw, default_kw in zip(custom_keywords[:len(default_keywords)], default_keywords):
        if custom_kw and str(custom_kw).strip() != "":
            keywords_list.append(custom_kw)
        else:
            keywords_list.append(default_kw)
    
    clean_keywords_str = "+".join(keywords_list)
    feedback = example_data.get(clean_keywords_str, example_data[default_keywords_str])
    return {
        "question": example_data["question"],
        "answer": example_data["answer"],
        "feedback": feedback
        }
    
    
    