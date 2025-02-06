# author: Dang Pham
# last modified: February 2025

import socket
import psutil

def first_available_port() -> int:
    """ Get the first available port on localhost.
        From: https://stackoverflow.com/questions/1365265/on-localhost-how-do-i-pick-a-free-port-number

        Returns
        -------
        port : int
            First available port on localhost
    """
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

# def first_available_port_in_range(port0:int, port1:int, server_path:str) -> int:
#     """ Get the first available port in a range.

#         Parameters
#         ----------
#         port0 : int
#             First port to check
#         port1 : int
#             Last port to check
#         server_path : str
#             Address of server. E.g. "http://localhost"

#         Returns
#         -------
#         port : int
#             First available port in the range
#     """
#     if server_path.startswith("http://"):
#         server_path = server_path.replace("http://", "")
        
#     for port in range(port0, port1):
#         if is_port_in_use(server_path, port) == False:
#             return port
#     return None

# def is_port_in_use(server_path:str, port: int) -> bool:
#     """ Check if a port is in use.
#         From: https://stackoverflow.com/questions/2470971/fast-way-to-test-if-a-port-is-in-use-using-python

#         Parameters
#         ----------
#         server_path : str
#             Address to check
#         port : int
#             Port to check

#         Returns
#         -------
#         is_port_in_use: bool
#             True if port is in use, False otherwise
#     """
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#     output = False
#     try:
#         s.bind((server_path, port))
#         output = False
#     except:
#         output = True
#     s.close()
#     return output

# def get_rebound_ports(port0:int, port1:int, server_path:str) -> list:
#     """ Get list of ports in use by Rebound servers.

#         Parameters
#         ----------
#         port0 : int
#             First port to check
#         port1 : int
#             Last port to check
#         server_path : str
#             Address of server. E.g. "http://localhost"

#         Returns
#         -------
#         rebound_ports : list
#             List of ports in use by Rebound servers
#     """
#     if server_path.startswith("http://"):
#         server_path = server_path.replace("http://", "")

#     # get list of ports in use
#     rebound_ports = []
#     for port in range(port0, port1):
#         if is_port_in_use(server_path, port):
#             rebound_ports.append(port)
#     return rebound_ports


# def close_port(port:int, server_path:str) -> None:
#     """ Release a port using a socket.

#         Parameters
#         ----------
#         port : int
#             Port to release
#         server_path : str
#             Address of server. E.g. "http://localhost"
#     """
#     if server_path.startswith("http://"):
#         server_path = server_path.replace("http://", "")

#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     s.bind((server_path, port))
#     s.close()
    
# def close_port(port):
#     for conn in psutil.net_connections(kind='inet'):
#         if conn.laddr.port == port:
#             print(f"Closing port {port} by terminating PID {conn.pid}")
#             process = psutil.Process(conn.pid)
#             process.terminate()