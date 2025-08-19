from typing import Dict, Any, Optional

class StateManager:
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def set_state(self, user_id: str, state: str, data: Optional[Dict[str, Any]] = None):
        if user_id not in self._states:
            self._states[user_id] = {}
        
        self._states[user_id]['current_state'] = state
        if data:
            self._states[user_id].update(data)
    
    def get_state(self, user_id: str) -> str:
        return self._states.get(user_id, {}).get('current_state', 'start')
    
    def get_user_data(self, user_id: str, key: str) -> Any:
        return self._states.get(user_id, {}).get(key)
    
    def set_user_data(self, user_id: str, key: str, value: Any):
        if user_id not in self._states:
            self._states[user_id] = {}
        self._states[user_id][key] = value
    
    def clear_user_state(self, user_id: str):
        if user_id in self._states:
            del self._states[user_id]

state_manager = StateManager()