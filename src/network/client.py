import socket
import threading
import json
import time

class NetworkClient:
    def __init__(self, host='localhost', port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.addr = None
        self.other_players = {} # {id: {pos: [x,y], status: '...'}}
        self.events = [] # List event yang diterima
        self.connected = False
        self.lock = threading.Lock()

    def connect(self):
        try:
            self.client.connect((self.host, self.port))
            # Handshake Awal
            data = self.client.recv(2048).decode()
            msg = json.loads(data)
            self.addr = msg.get('id')
            self.is_host = msg.get('is_host', False) # Simpan Status Host
            self.connected = True
            print(f"[NETWORK] Terhubung sebagai {self.addr} (Host: {self.is_host})")
            
            # Mulai thread listener
            self.thread = threading.Thread(target=self.listen)
            self.thread.daemon = True
            self.thread.start()
            return True
        except Exception as e:
            print(f"[NETWORK] Gagal Terhubung: {e}")
            return False

    def listen(self):
        while self.connected:
            try:
                # Terima buffer
                data = self.client.recv(4096).decode('utf-8')
                if not data:
                    break
                
                packets = data.split('\n')
                for packet in packets:
                    if not packet: continue
                    try:
                        msg = json.loads(packet)
                        
                        # Handle Update State
                        if 'players' in msg:
                            with self.lock:
                                # Update player lain, kecuali diri sendiri
                                raw_players = msg['players']
                                if self.addr in raw_players:
                                    del raw_players[self.addr]
                                self.other_players = raw_players
                                
                        # Handle Event (Broadcast dari server)
                        elif 'event' in msg:
                             evt_type = msg.get('event')
                             
                             # Migrasi Host
                             if evt_type == 'host_migration':
                                 new_host = msg.get('new_host')
                                 if new_host == self.addr:
                                     self.is_host = True
                                     print(f"[NETWORK] Anda sekarang adalah HOST.")
                             
                             # Jangan proses event sendiri jika dipantulkan balik
                             if msg.get('sender') != self.addr:
                                 with self.lock:
                                     self.events.append(msg)
                                     
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                print(f"[NETWORK] Error receiving: {e}")
                self.connected = False
                break

    def send_state(self, state):
        """
        Kirim dict state: {'pos': (x, y), 'status': 'run_down', 'char_type': 'adventurer'}
        """
        if not self.connected: return
        
        try:
            data = json.dumps(state) + '\n'
            self.client.send(data.encode('utf-8'))
        except socket.error as e:
            print(f"[NETWORK] Error Kirim: {e}")
            self.connected = False

    def send_event(self, event_type, data={}):
        """
        Kirim sebuah event.
        Otomatis bungkus dengan 'type': 'event' dan 'event': event_type.
        """
        if not self.connected: return
        
        payload = {
            'event': event_type,
            'sender': self.addr,
            **data
        }
        try:
            msg = json.dumps(payload) + '\n'
            self.client.send(msg.encode('utf-8'))
        except:
            self.connected = False

    def disconnect(self):
        self.connected = False
        self.client.close()
