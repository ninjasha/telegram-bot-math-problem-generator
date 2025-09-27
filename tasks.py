import json
from pathlib import Path
from typing import List, Dict, Union

### Task manager  ###
class TaskManager:
    def __init__(self):                                                     # Loading .json files
        self.tasks_path = Path(__file__).parent / 'tasks.json'
        self.examples_path = Path(__file__).parent / 'examples.json'
        self.tasks_data = self._load_data(self.tasks_path)
        self.examples_data = self._load_data(self.examples_path)
    
    def _load_data(self, file_path: Path) -> Dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        
    def get_elements(self) -> List[str]:                                    # Getting chosen options
        return self.tasks_data.get("Элементы", [])
    
    def get_types(self) -> Dict[str, List[str]]:
        return self.tasks_data.get("Типы", {})
    
    def get_type_options(self, type_name: str) -> List[str]:
        return self.tasks_data.get("Типы", {}).get(type_name, [])
    
    def get_category(self, category_name: str) -> List[str]:
        return self.tasks_data.get("Параметры", {}).get(category_name, [])
    
    def get_examples(self, task_type: str, subtype: str) -> List[str]:
        return self.examples_data.get(task_type, {}).get(subtype, [])
    

    def add_template(self, template: str) -> bool:                          # Adding and saving tamplates
        if "Шаблоны" not in self.tasks_data.get("Параметры", {}):
            self.tasks_data["Параметры"]["Шаблоны"] = []
        self.tasks_data["Параметры"]["Шаблоны"].append(template)
        self._save_data()
        return True
    
    def _save_data(self):
        with open(self.tasks_path, 'w', encoding='utf-8') as f:
            json.dump(self.tasks_data, f, ensure_ascii=False, indent=2)

task_manager = TaskManager()