import json
import os
import uuid
from pathlib import Path
from netcheck.core.models import CustomTarget, CheckType

class TargetManager:
    def __init__(self):
        if os.name == 'nt':
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            self.config_dir = Path(appdata) / 'NetCheck'
        else:
            self.config_dir = Path.home() / '.netcheck'
            
        self.targets_file = self.config_dir / 'targets.json'
        self._targets: list[CustomTarget] = []
        
        self.load()
        
    def load(self):
        if self.targets_file.exists():
            try:
                with open(self.targets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._targets = []
                    for t in data:
                        check_type_val = t.get('check_type')
                        try:
                            check_type = CheckType(check_type_val)
                        except ValueError:
                            check_type = CheckType.PING
                            
                        target = CustomTarget(
                            id=t.get('id', str(uuid.uuid4())),
                            name=t.get('name', ''),
                            host=t.get('host', ''),
                            check_type=check_type,
                            port=t.get('port'),
                            enabled=t.get('enabled', True)
                        )
                        self._targets.append(target)
            except Exception:
                pass
                
    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = []
        for t in self._targets:
            data.append({
                'id': t.id,
                'name': t.name,
                'host': t.host,
                'check_type': t.check_type.value,
                'port': t.port,
                'enabled': t.enabled
            })
        with open(self.targets_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    def get_all(self) -> list[CustomTarget]:
        return self._targets
        
    def get_enabled(self) -> list[CustomTarget]:
        return [t for t in self._targets if t.enabled]
        
    def add(self, target: CustomTarget):
        if not target.id:
            target.id = str(uuid.uuid4())
        self._targets.append(target)
        self.save()
        
    def update(self, target: CustomTarget):
        for i, t in enumerate(self._targets):
            if t.id == target.id:
                self._targets[i] = target
                self.save()
                return
                
    def delete(self, target_id: str):
        self._targets = [t for t in self._targets if t.id != target_id]
        self.save()

target_manager = TargetManager()
