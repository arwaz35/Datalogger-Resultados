import json
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
MOTOS_FILE = os.path.join(DATA_DIR, 'motos.json')
PILOTOS_FILE = os.path.join(DATA_DIR, 'pilotos.json')
LUGARES_FILE = os.path.join(DATA_DIR, 'lugares.json')

class DataManager:
    def __init__(self):
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        if not os.path.exists(MOTOS_FILE):
            with open(MOTOS_FILE, 'w') as f:
                json.dump([], f)
        if not os.path.exists(PILOTOS_FILE):
            with open(PILOTOS_FILE, 'w') as f:
                json.dump([], f)
        if not os.path.exists(LUGARES_FILE):
            with open(LUGARES_FILE, 'w') as f:
                json.dump([], f)

    def load_motos(self):
        try:
            with open(MOTOS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []

    def save_motos(self, motos):
        with open(MOTOS_FILE, 'w') as f:
            json.dump(motos, f, indent=4)

    def add_moto(self, moto_data):
        motos = self.load_motos()
        motos.append(moto_data)
        self.save_motos(motos)

    def update_moto(self, index, moto_data):
        motos = self.load_motos()
        if 0 <= index < len(motos):
            motos[index] = moto_data
            self.save_motos(motos)

    def delete_moto(self, index):
        motos = self.load_motos()
        if 0 <= index < len(motos):
            del motos[index]
            self.save_motos(motos)

    def load_pilotos(self):
        try:
            with open(PILOTOS_FILE, 'r') as f:
                data = json.load(f)
                
            # Migration check: if it's a list of strings, convert to dicts
            migrated_data = []
            modified = False
            for item in data:
                if isinstance(item, str):
                    migrated_data.append({"nombre": item, "peso": 0})
                    modified = True
                else:
                    migrated_data.append(item)
                    
            if modified:
                self.save_pilotos(migrated_data)
                
            return migrated_data
        except:
            return []

    def save_pilotos(self, pilotos):
        with open(PILOTOS_FILE, 'w') as f:
            json.dump(pilotos, f, indent=4)

    def add_piloto(self, nombre, peso=0):
        pilotos = self.load_pilotos()
        if not any(p.get('nombre') == nombre for p in pilotos): # Prevent duplicates
            pilotos.append({"nombre": nombre, "peso": peso})
            self.save_pilotos(pilotos)

    def update_piloto(self, old_nombre, new_nombre, new_peso):
        pilotos = self.load_pilotos()
        for p in pilotos:
            if p.get('nombre') == old_nombre:
                p['nombre'] = new_nombre
                p['peso'] = new_peso
                break
        self.save_pilotos(pilotos)

    def delete_piloto(self, nombre):
        pilotos = self.load_pilotos()
        pilotos = [p for p in pilotos if p.get('nombre') != nombre]
        self.save_pilotos(pilotos)

    # --- LUGARES METHODS ---
    def load_lugares(self):
        try:
            with open(LUGARES_FILE, 'r') as f:
                return json.load(f)
        except:
            return []

    def save_lugares(self, lugares):
        with open(LUGARES_FILE, 'w') as f:
            json.dump(lugares, f, indent=4)

    def add_lugar(self, lugar_data):
        lugares = self.load_lugares()
        lugares.append(lugar_data)
        self.save_lugares(lugares)

    def delete_lugar(self, index):
        lugares = self.load_lugares()
        if 0 <= index < len(lugares):
            del lugares[index]
            self.save_lugares(lugares)

    # --- RANKING METHODS ---
    RANKING_FILE = os.path.join(DATA_DIR, 'ranking.json')

    def load_ranking(self):
        try:
            if not os.path.exists(self.RANKING_FILE):
                return []
            with open(self.RANKING_FILE, 'r') as f:
                return json.load(f)
        except:
            return []

    def save_ranking(self, data):
        with open(self.RANKING_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def add_ranking_entry(self, entry):
        """
        Adds a single ranking entry.
        entry: dict with keys matching the requirement.
        """
        ranking = self.load_ranking()
        ranking.append(entry)
        self.save_ranking(ranking)

    def delete_ranking_entry(self, entry_to_delete):
        """
        Deletes a ranking entry that matches the provided dictionary.
        """
        ranking = self.load_ranking()
        # Filter out the entry. Using list comprehension for simplicity.
        # We assume exacta match of the dictionary.
        new_ranking = [r for r in ranking if r != entry_to_delete]
        
        if len(new_ranking) < len(ranking):
            self.save_ranking(new_ranking)
            return True
        return False
