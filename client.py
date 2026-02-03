# This program was modified by lynneth / n01424240
import socket
import argparse
import time
import os
import struct

def run_client(target_ip, target_port, input_file):
    # 1. Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    server_address = (target_ip, target_port)

    print(f"[*] Sending file '{input_file}' to {target_ip}:{target_port}")

    if not os.path.exists(input_file):
        print(f"[!] Error: File '{input_file}' not found.")
        return

    try:
        sequence_number = 0
        with open(input_file, 'rb') as f:
            while True:
                # Read a chunk of the file
                CHUNK_SIZE = 1400

                chunk = f.read(CHUNK_SIZE) # 4KB chunks
                
                if not chunk:
                    # End of file reached
                    break

                header = struct.pack('!I', sequence_number)
                packet = header + chunk

                acked = False
                while not acked:
                    try:
                        # Send the chunk
                        sock.sendto(packet, server_address)

                        data, addr = sock.recvfrom(1024)
                        if len(data) == 7 and data[:3] == b'ACK':
                            ack_seq = struct.unpack('!I', data[3:7])[0]
                            if ack_seq == sequence_number:
                                acked = True
                    except socket.timeout:
                        print(f"[!] timeout: retransmitting packet {sequence_number}...")
                        
                sequence_number += 1
                
                # Optional: Small sleep to prevent overwhelming the OS buffer locally
                # (In a perfect world, we wouldn't need this, but raw UDP is fast!)

        # Send empty packet to signal "End of File"
        header = struct.pack('!I', sequence_number)
        eof_packet = header + b''

        print("[*] Sending EOF signal...")
        acked = False
        while not acked:
            try:
                sock.sendto(eof_packet, server_address)
                data, addr = sock.recvfrom(1024)
                if len(data) == 7 and data[:3] == b'ACK':
                    ack_seq = struct.unpack('!I', data[3:7])[0]
                    if ack_seq == sequence_number:
                        acked = True
            except socket.timeout:
                print("[!] Timeout: Resending EOF...")

        print("[*] File transmission complete.")

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naive UDP File Sender")
    parser.add_argument("--target_ip", type=str, default="127.0.0.1", help="Destination IP (Relay or Server)")
    parser.add_argument("--target_port", type=int, default=12000, help="Destination Port")
    parser.add_argument("--file", type=str, required=True, help="Path to file to send")
    args = parser.parse_args()

    run_client(args.target_ip, args.target_port, args.file)