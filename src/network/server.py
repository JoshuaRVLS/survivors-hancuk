import socket
import threading
import json
import time

# Konfigurasi
HOST = '0.0.0.0'
PORT = 5555

class Server:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen()
        self.clients = {} # {addr: conn}
        self.player_states = {} # {addr: state_dict}
        self.running = True
        
        print(f"[SERVER] Jalan di {HOST}:{PORT}")

    def broadcast_state(self):
        """Kirim state pemain ke semua client secara berkala"""
        while self.running:
            if not self.clients:
                time.sleep(0.1)
                continue
                
            # Siapkan paket state
            # Format: {'players': {addr_str: {x, y, status, ...}}}
            state_packet = json.dumps({'players': self.player_states}).encode('utf-8')
            
            # Broadcast
            disconnected = []
            for addr, conn in self.clients.items():
                try:
                    # Protokol sederhana: kirim JSON mentah dengan delimiter baris baru
                    conn.sendall(state_packet + b'\n')
                except:
                    disconnected.append(addr)
            
            # Bersihkan koneksi yang putus
            for addr in disconnected:
                self.handle_disconnect(addr)
                
            time.sleep(1/30) # 30 Tick Rate

    def handle_client(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} terhubung.")
        
        # Handshake Awal (Opsional)
        addr_str = str(addr)
        self.clients[addr_str] = conn
        self.player_states[addr_str] = {'pos': (0, 0), 'status': 'idle_down'}
        
        # Tentukan Host (Koneksi pertama atau jika tidak ada host)
        is_host = len(self.clients) == 1
        
        # Kirim Handshake
        conn.send(json.dumps({'message': 'Welcome', 'id': addr_str, 'is_host': is_host}).encode('utf-8'))
        
        if is_host: print(f"[HOST] Diberikan ke {addr_str}")
        
        while self.running:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                
                # Parse data yang diterima
                # Asumsi client kirim json dengan delimiter \n
                packets = data.decode('utf-8').split('\n')
                for packet in packets:
                    if not packet: continue
                    try:
                        msg = json.loads(packet)
                        
                        # Cek apakah Event atau State
                        if 'event' in msg:
                            # Langsung Broadcast Event
                            self.broadcast_event(msg)
                        else:
                            # Update State
                            self.player_states[addr_str].update(msg)
                            
                    except json.JSONDecodeError:
                        pass
                        
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[ERROR] {addr}: {e}")
                break
        
        self.handle_disconnect(addr_str)
        conn.close()

    def broadcast_event(self, event_msg):
        """Kirim event ke semua client segera"""
        packet = (json.dumps(event_msg) + '\n').encode('utf-8')
        for conn in self.clients.values():
            try:
                conn.sendall(packet)
            except:
                pass

    def handle_disconnect(self, addr_str):
        # Perlu tahu apakah client ini adalah host untuk migrasi
        
        if addr_str in self.clients:
            print(f"[DISCONNECT] {addr_str} putus.")
            del self.clients[addr_str]
        if addr_str in self.player_states:
            del self.player_states[addr_str]
            
        # Re-assign host jika perlu
        # Jika Host disconnect, ambil client berikutnya sebagai host baru
        if self.clients:
             new_host = sorted(self.clients.keys())[0]
             print(f"[HOST] Migrasi ke {new_host}")
             self.broadcast_event({'event': 'host_migration', 'new_host': new_host})

    def start(self):
        # Mulai thread broadcast
        broadcast_thread = threading.Thread(target=self.broadcast_state)
        broadcast_thread.start()
        
        print("[SERVER] Menunggu koneksi...")
        while self.running:
            try:
                conn, addr = self.server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.start()
                print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")
            except KeyboardInterrupt:
                self.running = False
                break

if __name__ == "__main__":
    s = Server()
    s.start()
