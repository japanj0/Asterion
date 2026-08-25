import sys
import os
import ssl
import json
import sqlite3
import threading
import socket
import hashlib
import time
import base64
import shutil
import html
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from crypto import CryptoManager, TransportCipher
import pygame
from io import BytesIO

SOUND_ALERT_MP3 = base64.b64decode("""SUQzAwAAAABIIlREQVQAAAAFAAAAMTQwM1RJTUUAAAAFAAAAMTc1NFBSSVYAABvoAABYTVAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS41LWMwMjEgNzkuMTU1MjQxLCAyMDEzLzExLzI1LTIxOjEwOjQwICAgICAgICAiPgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iCiAgICB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIgogICAgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiCiAgICB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iCiAgICB4bWxuczp4bXBETT0iaHR0cDovL25zLmFkb2JlLmNvbS94bXAvMS4wL0R5bmFtaWNNZWRpYS8iCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpiZXh0PSJodHRwOi8vbnMuYWRvYmUuY29tL2J3Zi9iZXh0LzEuMC8iCiAgIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MmYxZjVkMGUtYzIyMS00MzI0LWEwNGUtMTc0OTk3YTRjZTRlIgogICB4bXBNTTpEb2N1bWVudElEPSIwNGRhNTY4Yy1kOTJiLTFiZjMtM2VhMS02YjA0MDAwMDAwNDkiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpiNmFkYmNkMS1hNzBmLTQ5NjUtYWNjMS00ODg2OWEwMDIxM2QiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMTQtMDMtMTRUMTc6NTQ6NTgtMDQ6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDE0LTAzLTE0VDE3OjU0OjU4LTA0OjAwIgogICB4bXA6Q3JlYXRlRGF0ZT0iMjAxNC0wMy0xNFQxNzo1NDoyOC0wNDowMCIKICAgeG1wRE06YXVkaW9TYW1wbGVSYXRlPSI0NDEwMCIKICAgeG1wRE06YXVkaW9TYW1wbGVUeXBlPSIxNkludCIKICAgeG1wRE06YXVkaW9DaGFubmVsVHlwZT0iU3RlcmVvIgogICB4bXBETTpzdGFydFRpbWVTY2FsZT0iMzAwMDAiCiAgIHhtcERNOnN0YXJ0VGltZVNhbXBsZVNpemU9IjEwMDEiCiAgIHhtcERNOnBhcnRPZkNvbXBpbGF0aW9uPSJmYWxzZSIKICAgZGM6Zm9ybWF0PSJNUDMiCiAgIGJleHQ6ZGVzY3JpcHRpb249Ik1VTFRJTUVESUEgQlVUVE9OIFRPTkFMIDAzIgogICBiZXh0Om9yaWdpbmF0b3I9IkFkb2JlIFN5c3RlbXMgSW5jIgogICBiZXh0Om9yaWdpbmF0aW9uRGF0ZT0iMjAxNC0wMy0wNSIKICAgYmV4dDpvcmlnaW5hdGlvblRpbWU9IjE5OjQ2OjExIgogICBiZXh0OnRpbWVSZWZlcmVuY2U9IjAiCiAgIGJleHQ6dmVyc2lvbj0iMSI+CiAgIDx4bXBNTTpIaXN0b3J5PgogICAgPHJkZjpTZXE+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSIyZWZmN2MyMi1lMzMyLTMwNTMtNTFiYS0xZGVlMDAwMDAwNzYiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMTRUMTc6NTQ6NTgtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9ImZkY2QyZDZhLWJmMmQtNDFkNS0wOTk0LWIxZTUwMDAwMDA3NiIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0xMlQxMzo1NS0wNDowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0iOTc3M2Q2ZDgtNTg0Mi00ZjdhLTBmYTAtZWIxZTAwMDAwMDc2IgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTA1VDE5OjQ2OjExLTA1OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOkJBQ0Q2NkE3OEYyMDY4MTE5MTA5QjNCMUQxRkI1RDE0IgogICAgICBzdEV2dDp3aGVuPSIyMDEzLTA0LTMwVDExOjAyOjM4LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIDUuNS4wIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvbWV0YWRhdGE7L2NvbnRlbnQiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6NDFDQkI4N0I5MTIwNjgxMTkxMDlCM0IxRDFGQjVEMTQiCiAgICAgIHN0RXZ0OndoZW49IjIwMTMtMDQtMzBUMTE6MTU6NDgtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgNS41LjAiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ibW9kaWZpZWQiCiAgICAgIHN0RXZ0OnBhcmFtZXRlcnM9InVua25vd24gbW9kaWZpY2F0aW9ucyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0iNTQxNDk3MzMtYjFhMC1mZDFkLTMwYWItZmUxOTAwMDAwMDc2IgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTA1VDE4OjU1OjI5LTA1OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU5ZDUzY2VjLTc0NjQtNGE3ZC04N2ZjLWMwYzM5MjYyYmYyNSIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0wNVQxOTo0NjoxMS0wNTowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDplNGIxZWE1MC02ZGU0LTRkZGEtOTZkYy0xZGZhMDFlMzA1ZjEiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMDVUMTk6NDY6MTEtMDU6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii9tZXRhZGF0YSIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDowMGY5ZDIyMi03ZmM3LTQxZTQtYTc3ZS02MTFmMGUzM2JiN2EiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMTJUMTM6NTUtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZDBmZGRjMDUtM2M3NC00MzAwLTlhYjItMzU2YTMwM2VmNjEwIgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTEyVDEzOjU1LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvbWV0YWRhdGEiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6MjEwYWI2NTAtNjkwZS00MzllLWI1NzktOWNkY2I1NjU3Y2JiIgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTE0VDE3OjU0OjU4LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjJmMWY1ZDBlLWMyMjEtNDMyNC1hMDRlLTE3NDk5N2E0Y2U0ZSIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0xNFQxNzo1NDo1OC0wNDowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iL21ldGFkYXRhIi8+CiAgICA8L3JkZjpTZXE+CiAgIDwveG1wTU06SGlzdG9yeT4KICAgPHhtcE1NOkRlcml2ZWRGcm9tCiAgICBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOmQwZmRkYzA1LTNjNzQtNDMwMC05YWIyLTM1NmEzMDNlZjYxMCIKICAgIHN0UmVmOmRvY3VtZW50SUQ9Ijc3ZjgyMzkxLWYyNjYtNzRlZS0wMTExLWFhZWUwMDAwMDA0OSIKICAgIHN0UmVmOm9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDoyZTEzYzBhNC00ZDFjLTRmNDQtYjcwYi1lZDQyYmI5OTBhNTYiLz4KICAgPHhtcERNOnN0YXJ0VGltZWNvZGUKICAgIHhtcERNOnRpbWVGb3JtYXQ9IjI5OTdEcm9wVGltZWNvZGUiCiAgICB4bXBETTp0aW1lVmFsdWU9IjAwOzAwOzAwOzAwIi8+CiAgIDx4bXBETTphbHRUaW1lY29kZQogICAgeG1wRE06dGltZVZhbHVlPSIwMDswMDswMDswMCIKICAgIHhtcERNOnRpbWVGb3JtYXQ9IjI5OTdEcm9wVGltZWNvZGUiLz4KICAgPHhtcERNOmR1cmF0aW9uCiAgICB4bXBETTp2YWx1ZT0iMyIKICAgIHhtcERNOnNjYWxlPSIxMDAxLzMwMDAwIi8+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz4AVEJQTQAAAAcAAAAxMjEuOTdUWUVSAAAABQAAADIwMjFUSVQyAAAABAAAAHNtcwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/+3BAAAAAAABLgAAACAAACXAAAAEBGAEYgAAAICGAY5AAAAQAggggYYkog6AAACkB+sPrD4CRVZUklKAIjen1HZOD0FgXYhAuCMU5byDkLVZ+AZw52k/FBVPqOQ0zrngPMsbPANM64+NQ2N/hXs9nkTL+PAQ9Rx8U974fx+CDviQ5rDDLX/qGJCQHgppuADxjGP/gFxcXd3d//d3/4rcuyAFwbnxUlnwLnwwXHA++TLn5eD/+U1EdsmPGQAQCDIhLwBH0lJKSAKYbGBhQaGMBoGMmuCWYA15pACGNg4BhIHA2ExekBbrpKqqIhxkF7bIVEaxIa4qhVwIjCjoSeanmu2IYyTvHrLCg1xbH8TdNf4rXWt//MLRTVw5pvKUf6E9Wd3LdSAqIIMiSyUTI3LwB9TVN+UsQ0T9B//twYIGAApYhS1U94AAwo3mqoKABDWidWvnHgBFBkSwrMpAC8JUUI3bFhS1rOPk7xpv/F2wJjEBnP3qEkb8k3/huTBPJUUoezeXVMN7/BD3HjsNhnVzzKG0oJdfv/F+TaASdtjt0AAF113qZVPrRBAFMIBszNhzjJ7AwBRxf6POtTTVoyWR5fb54/VsN7BnxFktw/x0q2tIUW94e5Pf4+t3xTN8Vvl/jX+P+mUJqbtolNySNyMIAfY3j+rXRkU/kQca4s1PVscbwyKNWXhgUpW7TuIob6lb4owt4hZupp9IiNP+/w7Br/8qoyy7ZXLYAAI+48pm5RL4ARPMWM0/+VgRT1+y2hRHaeV8JVTwnG8RuncY1NS0Qmot1skkk5qbIos7qVU9SkbO9d/WTWURRcbaUaBAEyI9nrf/7cGBsgAJ6JlVvceAKOeSrLeygAYh0l1OuPalg45KrtUSpLgCdEDGhQaZFUW2TRlmE4bfhb6lhtbAiOPOXQ4lJhWIh6WPPkLXpdfb4kv//UFRVqVQsGwuVlXnJ99FbzJysOhkYTUtytjeXNzKpIzsn94UR1AnsYLMQLBC003WpaK1utm1df/8xf/8ee6//9BzKcttm3owA/Ggt67quInJOfHUy2rumLy2x7Zpj6zvTs9BLBAx2Qw81GYxmbRW0v/Xml//5dpW/6pMB6YOgmbpYNuS8wHoMpKAwFd5QuSVfMLCjFlZfxXkZilgsUCNSO+hzkmDVh4ejVPYfEysW/6df0R////6FfaWNsIf21u9GAH4TX1JfDCc7BQ0cfX2WtBGNtWekgcrDk2pIA4UTIxVdbHNBa11I91r/+3BgdAAB+SXTS49qXDVkyq1p50sIeM1NLb1LcN4TKfWkNSwJqt/mRC//oEVkEWZnj/6gACIqgbx/qVgEPuKBYwo3AiUcGicSwhStakruJGnhbhbc4CkqYLI4lyUAI0uFtRw1MnOorKalpoJP/Rrov+XnSaATbn/CBhGcN4Q3SM/GFAswVhLKtisDLvTFGBDGMxKLAlCEYmKKaLmTWpOkipJ1srSZV9fkwj//yzsZLttkkAAAgxB1rDuu+sAw8uwBW4BiqVzFvFPxRlGuS3LpgP5XLbTYwmoaiuG6k2+o4Z7pytzPDLH79PS6u4jVX5P660VbdbZGGADhWNDDoAnALSAhVAREpSjisoq3CgNHpz2ftDc2MR+GCCRFwnqNkpsqig7qr7tqf/5ONv/5UHKyZrbJIgAAvov0//twYIaAAjgl0ntvklg6JMpcYG1LiHhpSa2/CTjykyn1NjUujlQJTiwQqcwIMMHPDhhFPQU8hscWFVgC0hyotVWRrRnytqxOLbFxScJUYjlq9K3zGjTLRQCoFj1uskpGTLbZJGAANV4ZkFPEIbYYIXA10Wey1RqjXP5FNWvJmSuHDdazIHSxcPqTszI9T1vU1G3V/Jy+uiOsk8AAEGgNE0tZhdstYWrNj4yWAPSiTGQBNUwkKGgFh0Cv9T5S25T13ChXfXgsuq2jWBglLYbC7roxZY+AADwaJ/5Yu9dipzFQy+WO0bXGjL7SGVWe1YatYzR6qtL/ypJoPHwgRUtRIEDr1YysCgENuqM3SAdZxC2orLsrc//////////////////////////////////////////////////7cGCQAAIrF9Brb3pMN0SqHWUtS8dATyOM7ecosInksY2g5P/////////////////////////////8gqMgAGF86WCXMNFAEwE10ke2e5D/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+3BgqQACngfGoHrIqhPg+MQHOBVAAAEuAAAAIAAAJcAAAAT///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////twQP+ACKgAS4AAAAgAAAlwAAABAAABLgAAACAAACXAAAAE/////////////////////////////////////////////////////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/7cED/gAioAEuAAAAIAAAJcAAAAQAAAS4AAAAgAAAlwAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABUQUcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAyMDE0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==""".strip())

class SoundPlayer:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    def play_alert(self):
        try:
            sound = pygame.mixer.Sound(BytesIO(SOUND_ALERT_MP3))
            sound.play()
        except:
            pass
_sound_player = None
def play_alert_sound():
    global _sound_player
    if _sound_player is None:
        _sound_player = SoundPlayer()
    _sound_player.play_alert()

def send_packet(sock, packet: dict):
    data = json.dumps(packet).encode('utf-8')
    header = len(data).to_bytes(4, byteorder='big')
    sock.sendall(header + data)

class PacketReader:
    MAX_BUFFER = 8 * 1024 * 1024
    def __init__(self):
        self.buffer = b''
    def feed(self, chunk: bytes):
        self.buffer += chunk
        if len(self.buffer) > self.MAX_BUFFER:
            raise ConnectionError()
    def pop_packets(self):
        packets = []
        while True:
            if len(self.buffer) < 4:
                break
            length = int.from_bytes(self.buffer[:4], byteorder='big')
            if length == 0 or length > 2 * 1024 * 1024:
                raise ConnectionError()
            if len(self.buffer) < 4 + length:
                break
            raw = self.buffer[4:4 + length]
            self.buffer = self.buffer[4 + length:]
            try:
                packets.append(json.loads(raw.decode('utf-8')))
            except:
                raise ConnectionError()
        return packets

os.makedirs("admin", exist_ok=True)
os.makedirs("database", exist_ok=True)
os.makedirs("files", exist_ok=True)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "127.0.0.1"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_self_signed_cert():
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import datetime
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "RU"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Moscow"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Moscow"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Asterion"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(
        key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(
        datetime.datetime.now(datetime.UTC)).not_valid_after(
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=3650)).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False).sign(key, hashes.SHA256())
    with open("admin/server.crt", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open("admin/server.key", "wb") as f:
        f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                  serialization.NoEncryption()))

crypto = None

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("database/messages.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()
        with self.lock:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_type TEXT,
                    from_user TEXT,
                    to_user TEXT,
                    message TEXT,
                    timestamp TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_type TEXT,
                    from_user TEXT,
                    to_user TEXT,
                    filename TEXT,
                    filepath TEXT,
                    filesize INTEGER,
                    timestamp TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS usb_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    event TEXT,
                    timestamp TEXT
                )
            ''')
            self.conn.commit()

    def save_message(self, chat_type, from_user, to_user, encrypted_message):
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "INSERT INTO messages (chat_type, from_user, to_user, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                (chat_type, from_user, to_user, encrypted_message, timestamp)
            )
            self.conn.commit()
            return timestamp

    def save_usb_event(self, username, event):
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "INSERT INTO usb_events (username, event, timestamp) VALUES (?, ?, ?)",
                (username, event, timestamp)
            )
            self.conn.commit()

    def save_file(self, chat_type, from_user, to_user, filename, filepath, filesize):
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "INSERT INTO files (chat_type, from_user, to_user, filename, filepath, filesize, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (chat_type, from_user, to_user, filename, filepath, filesize, timestamp)
            )
            self.conn.commit()
            return timestamp

    def get_general_messages(self):
        with self.lock:
            self.cursor.execute(
                "SELECT from_user, to_user, message, timestamp FROM messages WHERE chat_type='general' ORDER BY timestamp"
            )
            return self.cursor.fetchall()

    def get_usb_events(self, limit=1000):
        with self.lock:
            self.cursor.execute(
                "SELECT username, event, timestamp FROM usb_events ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return self.cursor.fetchall()

    def get_general_files(self):
        with self.lock:
            self.cursor.execute(
                "SELECT from_user, to_user, filename, filepath, filesize, timestamp FROM files WHERE chat_type='general' ORDER BY timestamp"
            )
            return self.cursor.fetchall()

    def get_private_messages(self, user1, user2):
        with self.lock:
            self.cursor.execute(
                """SELECT from_user, to_user, message, timestamp FROM messages
                   WHERE chat_type='private' AND ((from_user=? AND to_user=?) OR (from_user=? AND to_user=?))
                   ORDER BY timestamp""",
                (user1, user2, user2, user1)
            )
            return self.cursor.fetchall()

    def get_private_files(self, user1, user2):
        with self.lock:
            self.cursor.execute(
                """SELECT from_user, to_user, filename, filepath, filesize, timestamp FROM files
                   WHERE chat_type='private' AND ((from_user=? AND to_user=?) OR (from_user=? AND to_user=?))
                   ORDER BY timestamp""",
                (user1, user2, user2, user1)
            )
            return self.cursor.fetchall()

    def get_all_messages_for_user(self, username):
        with self.lock:
            self.cursor.execute(
                """SELECT chat_type, from_user, to_user, message, timestamp FROM messages
                   WHERE chat_type='general' OR (chat_type='private' AND (to_user=? OR from_user=?))
                   ORDER BY timestamp""",
                (username, username)
            )
            return self.cursor.fetchall()

    def get_all_files_for_user(self, username):
        with self.lock:
            self.cursor.execute(
                """SELECT chat_type, from_user, to_user, filename, filepath, filesize, timestamp FROM files
                   WHERE chat_type='general' OR (chat_type='private' AND (to_user=? OR from_user=?))
                   ORDER BY timestamp""",
                (username, username)
            )
            return self.cursor.fetchall()

    def get_all_general_messages(self):
        with self.lock:
            self.cursor.execute(
                "SELECT from_user, to_user, message, timestamp FROM messages WHERE chat_type='general' ORDER BY timestamp"
            )
            return self.cursor.fetchall()

    def get_all_users_with_private_chat(self):
        with self.lock:
            self.cursor.execute(
                """SELECT DISTINCT from_user FROM messages
                   WHERE chat_type='private' AND to_user='Director' AND from_user != 'Director'
                   UNION
                   SELECT DISTINCT to_user FROM messages
                   WHERE chat_type='private' AND from_user='Director' AND to_user != 'Director'
                   ORDER BY from_user"""
            )
            return [row[0] for row in self.cursor.fetchall()]

    def get_file_by_name_and_sender(self, filename, from_user, to_user, chat_type):
        with self.lock:
            self.cursor.execute(
                "SELECT id, filepath, filesize FROM files WHERE filename=? AND from_user=? AND to_user=? AND chat_type=?",
                (filename, from_user, to_user, chat_type)
            )
            return self.cursor.fetchone()

db = DatabaseManager()

class ServerThread(QThread):
    message_received = pyqtSignal(str, str, str, str)
    screen_received = pyqtSignal(str, str)
    user_connected = pyqtSignal(str)
    user_disconnected = pyqtSignal(str)
    auth_failed = pyqtSignal(str)
    stop_screen_requested = pyqtSignal(str)
    file_received = pyqtSignal(str, str, str, str, int, str)
    pending_user_connected = pyqtSignal(str)
    pending_user_removed = pyqtSignal(str)
    usb_event_received = pyqtSignal(str, str, str)
    usb_info_response_received = pyqtSignal(str, list)

    def __init__(self, server_password, port=5555):
        super().__init__()
        self.port = port
        self.clients = {}
        self.pending_clients = {}
        self.approved_users = set()
        self.running = True
        self.server_password_hash = hash_password(server_password)
        self.heartbeat_interval = 10
        self._heartbeat_thread = None
        self.transport = TransportCipher(server_password)
        self.file_receives = {}
        self.auth_attempts = {}
        self.blocked_ips = set()
        self.max_attempts = 5
        self.max_connections = 5
        self.max_threads = 50
        self.connection_tracker = {}
        self._conn_history = {}
        self._tcp_history = {}
        self.blocker_password_hash = None

    def run(self):
        if not os.path.exists("admin/server.crt") or not os.path.exists("admin/server.key"):
            generate_self_signed_cert()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', self.port))
        self.server.listen(100)
        self.server.settimeout(1.0)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain("admin/server.crt", "admin/server.key")
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        while self.running:
            try:
                if threading.active_count() > self.max_threads:
                    time.sleep(0.1)
                    continue
                client_socket, addr = self.server.accept()
                client_ip = addr[0]
                if client_ip in self.blocked_ips:
                    client_socket.close()
                    continue
                now = time.time()
                if client_ip not in self._tcp_history:
                    self._tcp_history[client_ip] = []
                self._tcp_history[client_ip] = [t for t in self._tcp_history[client_ip] if now - t < 60]
                if len(self._tcp_history[client_ip]) > 10:
                    client_socket.close()
                    continue
                self._tcp_history[client_ip].append(now)
                if client_ip not in self.connection_tracker:
                    self.connection_tracker[client_ip] = 0
                self.connection_tracker[client_ip] += 1
                if self.connection_tracker[client_ip] > self.max_connections:
                    client_socket.close()
                    continue
                try:
                    ssl_sock = context.wrap_socket(client_socket, server_side=True)
                except:
                    client_socket.close()
                    continue
                ssl_sock.settimeout(3.0)
                try:
                    header = ssl_sock.recv(4)
                    if len(header) != 4:
                        raise ValueError()
                    length = int.from_bytes(header, 'big')
                    if length == 0 or length > 4096:
                        raise ValueError()
                    payload = b''
                    while len(payload) < length:
                        chunk = ssl_sock.recv(length - len(payload))
                        if not chunk:
                            raise ValueError()
                        payload += chunk
                    auth_packet = json.loads(payload.decode('utf-8'))
                except:
                    ssl_sock.close()
                    continue
                finally:
                    ssl_sock.settimeout(None)
                username = auth_packet.get('username')
                password = auth_packet.get('password')
                if not username or not password:
                    ssl_sock.close()
                    continue
                if password == self.server_password_hash:
                    if username in self.approved_users or username.lower() == "director":
                        send_packet(ssl_sock, {'status': 'flag{0ff_th3_wa11}'})
                        ssl_sock.close()
                    else:
                        send_packet(ssl_sock, {'status': 'pending'})
                        self.pending_clients[username] = {'socket': ssl_sock, 'addr': addr}
                        self.pending_user_connected.emit(username)
                        client_thread = threading.Thread(target=self.handle_client, args=(ssl_sock, username))
                        client_thread.daemon = True
                        client_thread.start()
                else:
                    if client_ip not in self.auth_attempts:
                        self.auth_attempts[client_ip] = 1
                    else:
                        self.auth_attempts[client_ip] += 1
                    if self.auth_attempts[client_ip] >= self.max_attempts:
                        self.blocked_ips.add(client_ip)
                        ssl_sock.close()
                        continue
                    ssl_sock.close()
                    self.auth_failed.emit(username)
            except socket.timeout:
                continue
            except Exception:
                break
    def _heartbeat_loop(self):
        while self.running:
            time.sleep(self.heartbeat_interval)
            if not self.running:
                break
            dead = []
            for username, info in list(self.clients.items()):
                try:
                    send_packet(info['socket'], {'type': 'ping'})
                except:
                    dead.append(username)
            for username in dead:
                try:
                    self.clients[username]['socket'].close()
                except:
                    pass
                if username in self.clients:
                    del self.clients[username]
                self.user_disconnected.emit(username)

    def handle_client(self, client_socket, username):
        client_socket.settimeout(60.0)
        reader = PacketReader()
        packet_times = []
        ALLOWED_TYPES = {
            'message', 'screen', 'stop_screen',
            'file_start', 'file_chunk', 'file_end', 'file_request',
            'usb_event', 'usb_info_response', 'pong'
        }
        try:
            while self.running:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                reader.feed(chunk)
                for packet in reader.pop_packets():
                    now = time.time()
                    packet_times = [t for t in packet_times if now - t < 1]
                    packet_times.append(now)
                    if len(packet_times) > 50:
                        return
                    ptype = packet.get('type')
                    if ptype not in ALLOWED_TYPES:
                        return
                    try:
                        is_pending = username in self.pending_clients
                        if ptype == 'message':
                            if is_pending:
                                continue
                            to_user = packet.get('to')
                            wire_message = packet.get('message')
                            message = self.transport.decrypt_text(wire_message)
                            encrypted = crypto.encrypt_message(message)
                            if to_user == 'general':
                                db.save_message('general', username, 'general', encrypted)
                                self.message_received.emit(username, encrypted, to_user, 'general')
                                decrypted = crypto.decrypt_message(encrypted)
                                for user, info in self.clients.items():
                                    if user != username:
                                        try:
                                            send_packet(info['socket'], {
                                                'type': 'message',
                                                'from': username,
                                                'message': self.transport.encrypt_text(decrypted),
                                                'to': 'general'
                                            })
                                        except:
                                            pass
                            else:
                                db.save_message('private', username, to_user, encrypted)
                                self.message_received.emit(username, encrypted, to_user, 'private')
                                if to_user in self.clients:
                                    decrypted = crypto.decrypt_message(encrypted)
                                    try:
                                        send_packet(self.clients[to_user]['socket'], {
                                            'type': 'message',
                                            'from': username,
                                            'message': self.transport.encrypt_text(decrypted),
                                            'to': to_user
                                        })
                                    except:
                                        pass
                        elif ptype == 'screen':
                            to_user = packet.get('to')
                            screen_data = self.transport.decrypt_text(packet.get('data'))
                            self.screen_received.emit(username, screen_data)
                        elif ptype == 'stop_screen':
                            self.stop_screen_requested.emit(username)
                        elif ptype == 'file_start':
                            if is_pending:
                                continue
                            to_user = packet.get('to')
                            filename = packet.get('filename')
                            filesize = packet.get('filesize')
                            total_chunks = packet.get('total_chunks')
                            chat_type = packet.get('chat_type')
                            file_id = packet.get('file_id')
                            if file_id in self.file_receives:
                                self.file_receives[file_id]['file'].close()
                                del self.file_receives[file_id]
                            safe_filename = f"{int(time.time())}_{username}_{filename}"
                            filepath = os.path.join("files", safe_filename)
                            f = open(filepath, "wb")
                            self.file_receives[file_id] = {
                                'file': f,
                                'filename': filename,
                                'safe_filename': safe_filename,
                                'filepath': filepath,
                                'filesize': filesize,
                                'chat_type': chat_type,
                                'from_user': username,
                                'to_user': to_user,
                                'total_chunks': total_chunks,
                                'received_chunks': 0
                            }
                        elif ptype == 'file_chunk':
                            if is_pending:
                                continue
                            file_id = packet.get('file_id')
                            chunk_index = packet.get('chunk_index')
                            chunk_token = packet.get('data')
                            if file_id in self.file_receives:
                                try:
                                    chunk_data = self.transport.decrypt_bytes(chunk_token)
                                    reencrypted_chunk = crypto.encrypt_file_bytes(chunk_data)
                                    length_prefix = len(reencrypted_chunk).to_bytes(4, "big")
                                    self.file_receives[file_id]['file'].write(length_prefix + reencrypted_chunk)
                                    self.file_receives[file_id]['received_chunks'] += 1
                                except Exception:
                                    pass
                        elif ptype == 'file_end':
                            if is_pending:
                                continue
                            file_id = packet.get('file_id')
                            if file_id in self.file_receives:
                                info = self.file_receives[file_id]
                                info['file'].close()
                                chat_type = info['chat_type']
                                from_user = info['from_user']
                                to_user = info['to_user']
                                filename = info['filename']
                                filepath = info['filepath']
                                filesize = info['filesize']
                                db.save_file(chat_type, from_user, to_user, filename, filepath, filesize)
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                del self.file_receives[file_id]
                                notify_data = {
                                    'type': 'file_notify',
                                    'from': from_user,
                                    'filename': filename,
                                    'filesize': filesize,
                                    'chat_type': chat_type,
                                    'timestamp': timestamp,
                                    'to': to_user
                                }
                                self.file_received.emit(from_user, to_user, filename, chat_type, filesize, timestamp)
                                if chat_type == 'general':
                                    for user, info in self.clients.items():
                                        try:
                                            send_packet(info['socket'], notify_data)
                                        except:
                                            pass
                                else:
                                    recipients = [from_user, to_user]
                                    for user in recipients:
                                        if user in self.clients:
                                            try:
                                                send_packet(self.clients[user]['socket'], notify_data)
                                            except:
                                                pass
                        elif ptype == 'file_request':
                            if is_pending:
                                continue
                            filename = packet.get('filename')
                            from_user = packet.get('from_user')
                            chat_type = packet.get('chat_type')
                            to_user = packet.get('to_user')
                            file_info = db.get_file_by_name_and_sender(filename, from_user, to_user, chat_type)
                            if file_info:
                                file_id_db, filepath, filesize = file_info
                                if os.path.exists(filepath):
                                    plain_data = crypto.read_encrypted_file(filepath)
                                    chunk_size = 1024 * 1024
                                    total_chunks = (len(plain_data) + chunk_size - 1) // chunk_size
                                    file_id_download = f"download_{int(time.time())}_{from_user}_{filename}"
                                    for i in range(total_chunks):
                                        try:
                                            data = plain_data[i * chunk_size:(i + 1) * chunk_size]
                                            data_token = self.transport.encrypt_bytes(data)
                                            dl_packet = {
                                                'type': 'file_download_chunk',
                                                'file_id': file_id_download,
                                                'filename': filename,
                                                'chunk_index': i,
                                                'total_chunks': total_chunks,
                                                'data': data_token
                                            }
                                            send_packet(client_socket, dl_packet)
                                            time.sleep(0.001)
                                        except Exception:
                                            break
                        elif ptype == 'usb_event':
                            if is_pending:
                                continue
                            encrypted_data = packet.get('data')
                            decrypted = self.transport.decrypt_text(encrypted_data)
                            db.save_usb_event(username, decrypted)
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            self.usb_event_received.emit(username, timestamp, decrypted)
                        elif ptype == 'usb_info_response':
                            encrypted_data = packet.get('data', '')
                            try:
                                decrypted = self.transport.decrypt_text(encrypted_data)
                                devices = json.loads(decrypted)
                            except Exception:
                                devices = []
                            self.usb_info_response_received.emit(username, devices)
                        elif ptype == 'pong':
                            pass
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            try:
                client_ip = client_socket.getpeername()[0]
                if client_ip in self.connection_tracker:
                    self.connection_tracker[client_ip] -= 1
                    if self.connection_tracker[client_ip] <= 0:
                        del self.connection_tracker[client_ip]
            except OSError:
                pass
            try:
                client_socket.close()
            except Exception:
                pass
            self.user_disconnected.emit(username)
            if username in self.clients:
                del self.clients[username]
            if username in self.pending_clients:
                del self.pending_clients[username]
            self.pending_user_removed.emit(username)

    def approve_user(self, username):
        if username in self.pending_clients:
            client_info = self.pending_clients[username]
            client_socket = client_info['socket']
            self.approved_users.add(username)
            addr = client_info['addr']
            try:
                send_packet(client_socket, {
                    'type': 'approved',
                    'blocker_hash': self.blocker_password_hash
                })
            except:
                pass
            self.clients[username] = {'socket': client_socket, 'addr': addr}
            del self.pending_clients[username]
            self.user_connected.emit(username)
            self.pending_user_removed.emit(username)

    def reject_user(self, username):
        if username in self.pending_clients:
            try:
                send_packet(self.pending_clients[username]['socket'], {'type': 'rejected'})
                self.pending_clients[username]['socket'].close()
            except:
                pass
            if username in self.pending_clients:
                del self.pending_clients[username]
            self.pending_user_removed.emit(username)

    def send_notification(self, to_user, message):
        if to_user in self.clients:
            try:
                send_packet(self.clients[to_user]['socket'], {
                    'type': 'notification',
                    'from': 'Director',
                    'message': self.transport.encrypt_text(message)
                })
                return True
            except:
                return False
        return False

    def send_history(self, username):
        if username in self.clients:
            try:
                history_messages = db.get_all_messages_for_user(username)
                history_files = db.get_all_files_for_user(username)
                history_data = []
                for chat_type, from_user, to_user, msg, ts in history_messages:
                    decrypted = crypto.decrypt_message(msg)
                    if chat_type == 'general':
                        target = 'general'
                    else:
                        target = to_user if from_user != username else from_user
                    history_data.append({
                        'type': 'message',
                        'chat_type': chat_type,
                        'from': from_user,
                        'to': target,
                        'message': self.transport.encrypt_text(decrypted),
                        'timestamp': ts
                    })
                for chat_type, from_user, to_user, filename, filepath, filesize, ts in history_files:
                    if chat_type == 'general':
                        target = 'general'
                    else:
                        target = to_user if from_user != username else from_user
                    history_data.append({
                        'type': 'file',
                        'chat_type': chat_type,
                        'from': from_user,
                        'to': target,
                        'filename': filename,
                        'filesize': filesize,
                        'timestamp': ts
                    })
                history_data.sort(key=lambda x: x['timestamp'])
                if history_data:
                    send_packet(self.clients[username]['socket'], {
                        'type': 'history',
                        'messages': history_data
                    })
            except:
                pass

    def stop(self):
        self.running = False
        for client in self.clients.values():
            try:
                client['socket'].close()
            except:
                pass
        for client in self.pending_clients.values():
            try:
                client['socket'].close()
            except:
                pass
        try:
            self.server.close()
        except:
            pass

class IpDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.update_ip()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        self.ip_label = QLabel("0.0.0.0")
        self.ip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ip_label.setStyleSheet("""
            color: #4a9a4a;
            font-size: 22px;
            font-weight: bold;
            background-color: #2d2d3a;
            padding: 12px;
            border-radius: 8px;
            border: 2px solid #4a6a8a;
        """)
        layout.addWidget(self.ip_label)
        self.setLayout(layout)
        self.setStyleSheet("background-color: #2d2d3a; border: none;")
    def update_ip(self):
        ip = get_local_ip()
        self.ip_label.setText(ip)

class ServerPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asterion - Пароль сервера")
        self.setFixedSize(450, 280)
        self.setStyleSheet("""
            QDialog { background-color: #2d2d3a; }
            QLabel { color: white; font-size: 15px; }
            QLineEdit {
                background-color: #3d3d4a;
                border: 1px solid #5a5a6a;
                border-radius: 6px;
                padding: 10px 12px;
                color: #e0e0e0;
                font-size: 15px;
            }
            QLineEdit:focus { border: 1px solid #4a6a8a; }
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                color: white;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #5a7a9a; }
            QPushButton:pressed { background-color: #3a5a7a; }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        title_label = QLabel("Asterion")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4a9a4a; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        sub_label = QLabel("Введите пароль сервера")
        sub_label.setStyleSheet("font-size: 16px; color: #8a8a9a; margin-bottom: 10px;")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self.accept)
        layout.addWidget(self.password_input)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_input.setMinimumHeight(40)
        self.confirm_input.returnPressed.connect(self.accept)
        layout.addWidget(self.confirm_input)
        layout.addSpacing(10)
        start_btn = QPushButton("Запустить сервер")
        start_btn.setMinimumHeight(45)
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn)
        self.setLayout(layout)
    MIN_PASSWORD_LENGTH = 10
    def get_password(self):
        pwd1 = self.password_input.text().strip()
        pwd2 = self.confirm_input.text().strip()
        if not pwd1 or not pwd2:
            return None, "Пароль не может быть пустым"
        if pwd1 != pwd2:
            return None, "Пароли не совпадают"
        if len(pwd1) % 2 != 0:
            return None, "Пароль должен содержать чётное количество символов"
        if len(pwd1) < self.MIN_PASSWORD_LENGTH:
            return None, f"Пароль должен содержать не менее {self.MIN_PASSWORD_LENGTH} символов"
        return pwd1, None

class BlockerPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asterion - Пароль блокировки")
        self.setFixedSize(500, 300)
        self.setStyleSheet("""
            QDialog { background-color: #2d2d3a; }
            QLabel { color: white; font-size: 15px; }
            QLineEdit {
                background-color: #3d3d4a;
                border: 1px solid #5a5a6a;
                border-radius: 6px;
                padding: 10px 12px;
                color: #e0e0e0;
                font-size: 15px;
            }
            QLineEdit:focus { border: 1px solid #4a6a8a; }
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                color: white;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #5a7a9a; }
            QPushButton:pressed { background-color: #3a5a7a; }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        title_label = QLabel("Asterion")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #c0392b; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        sub_label = QLabel("Установите пароль для разблокировки блокировщика")
        sub_label.setStyleSheet("font-size: 16px; color: #8a8a9a; margin-bottom: 10px;")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Пароль блокировки")
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self.accept)
        layout.addWidget(self.password_input)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_input.setMinimumHeight(40)
        self.confirm_input.returnPressed.connect(self.accept)
        layout.addWidget(self.confirm_input)
        layout.addSpacing(10)
        start_btn = QPushButton("Продолжить")
        start_btn.setMinimumHeight(45)
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn)
        self.setLayout(layout)

    def get_password(self):
        pwd1 = self.password_input.text().strip()
        pwd2 = self.confirm_input.text().strip()
        if not pwd1 or not pwd2:
            return None, "Пароль не может быть пустым"
        if pwd1 != pwd2:
            return None, "Пароли не совпадают"
        if len(pwd1) < 8:
            return None, "Пароль должен содержать не менее 8 символов"
        return pwd1, None

class StegoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setAcceptDrops(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        hint = QLabel("Перетащите файл сюда или нажмите кнопку")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #8a8a9a; font-size: 16px; padding: 40px;")
        layout.addWidget(hint)
        btn = QPushButton("Выбрать файл")
        btn.setMinimumHeight(45)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                color: white;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #5a7a9a; }
            QPushButton:pressed { background-color: #3a5a7a; }
        """)
        btn.clicked.connect(self.load_file)
        layout.addWidget(btn)
        self.result = QTextBrowser()
        self.result.setStyleSheet("""
            QTextBrowser {
                background-color: #3d3d4a;
                border: 1px solid #4a4a5a;
                border-radius: 6px;
                padding: 12px;
                color: #e0e0e0;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.result)
        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.analyze(url.toLocalFile())
                break

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if path:
            self.analyze(path)

    def analyze(self, path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            result = self.parent_window.extract_stego(data)
            if result:
                self.result.setText(f"Обнаружена цепочка:\n{result}")
            else:
                self.result.setText("Стеганографические метаданные не обнаружены")
        except Exception as e:
            self.result.setText(f"Ошибка чтения файла: {e}")

class MainWindow(QMainWindow):
    def __init__(self, server_password, blocker_password_hash):
        super().__init__()
        self.server_password = server_password
        self.blocker_password_hash = blocker_password_hash
        self.server_thread = None
        self.current_chat = "general"
        self.current_screen_user = None
        self.private_chats = {}
        self.is_processing_link = False
        self.init_ui()
        self.load_general_history()
        self.load_private_chats()
        self.load_usb_history()
        self.start_server()

    def load_usb_history(self):
        events = db.get_usb_events(limit=1000)
        self.usb_display.clear()
        for username, event, timestamp in reversed(events):
            line = f"{username}, {timestamp}: {event}"
            self.append_chat_line(self.usb_display, line)

    def extract_stego(self, data):
        enc = None
        if data.startswith(b'\x89PNG\r\n\x1a\n'):
            i = 8
            while i < len(data):
                l = int.from_bytes(data[i:i+4], 'big')
                t = data[i+4:i+8]
                if t == b'tEXt':
                    c = data[i+8:i+8+l]
                    if c.startswith(b'asterion\x00'):
                        pb = c[9:]
                        pl = int.from_bytes(pb[:4], 'big')
                        enc = pb[4:4+pl].decode('utf-8')
                        break
                i += 12 + l
        elif data.startswith(b'\xff\xd8\xff'):
            i = 2
            while i < len(data) - 1:
                if data[i] == 0xFF and data[i+1] == 0xFE:
                    l = int.from_bytes(data[i+2:i+4], 'big')
                    c = data[i+4:i+4+l-2]
                    if c.startswith(b'asterion\x00'):
                        pb = c[9:]
                        pl = int.from_bytes(pb[:4], 'big')
                        enc = pb[4:4+pl].decode('utf-8')
                        break
                elif data[i] == 0xFF and data[i+1] not in (0x00, 0xD9):
                    l = int.from_bytes(data[i+2:i+4], 'big')
                    i += 2 + l
                else:
                    i += 1
        elif data.startswith(b'GIF8'):
            i = 0
            while i < len(data) - 1:
                if data[i] == 0x21 and data[i+1] == 0xFE:
                    i += 2
                    p = []
                    while True:
                        if i >= len(data):
                            break
                        s = data[i]
                        i += 1
                        if s == 0:
                            break
                        p.append(data[i:i+s])
                        i += s
                    c = b''.join(p)
                    if c.startswith(b'asterion\x00'):
                        pb = c[9:]
                        pl = int.from_bytes(pb[:4], 'big')
                        enc = pb[4:4+pl].decode('utf-8')
                        break
                i += 1
        else:
            try:
                text = data.decode('utf-8')
                bits = []
                for ch in text:
                    if ch == '\u200b':
                        bits.append(0)
                    elif ch == '\u200c':
                        bits.append(1)
                if len(bits) >= 32:
                    l = 0
                    for i in range(32):
                        l = (l << 1) | bits[i]
                    if 0 < l <= (len(bits) - 32) // 8:
                        eb = bits[32:32+l*8]
                        bb = bytearray(l)
                        for i in range(l):
                            b = 0
                            for j in range(8):
                                b = (b << 1) | eb[i*8+j]
                            bb[i] = b
                        enc = bytes(bb).decode('utf-8')
            except:
                try:
                    l = int.from_bytes(data[-4:], 'big')
                    if 0 < l <= len(data) - 4:
                        enc = data[-(4+l):-4].decode('utf-8')
                except:
                    pass
        if enc:
            return self.server_thread.transport.decrypt_text(enc)
        return None
    def append_chat_line(self, chat_display, line):
        cursor = chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not chat_display.document().isEmpty():
            cursor.insertBlock()
        cursor.setCharFormat(QTextCharFormat())
        cursor.insertHtml(line)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.setCharFormat(QTextCharFormat())
        chat_display.setTextCursor(cursor)
        chat_display.ensureCursorVisible()

    def load_private_chats(self):
        users = db.get_all_users_with_private_chat()
        for username in users:
            chat_widget = self.create_chat_widget()
            self.chat_tabs.addTab(chat_widget, username)
            self.private_chats[username] = chat_widget
            history_messages = db.get_private_messages("Director", username)
            history_files = db.get_private_files("Director", username)
            combined = []
            for from_user, to_user, msg, ts in history_messages:
                try:
                    decrypted = crypto.decrypt_message(msg)
                    safe_from = html.escape(from_user)
                    safe_decrypted = html.escape(decrypted)
                    safe_ts = html.escape(ts)
                    display_name = "Я" if from_user == "Director" else safe_from
                    combined.append((ts, f"[{safe_ts}] {display_name}: {safe_decrypted}"))
                except:
                    safe_from = html.escape(from_user)
                    safe_ts = html.escape(ts)
                    combined.append((ts, f"[{safe_ts}] {safe_from}: [Зашифровано]"))
            for from_user, to_user, filename, filepath, filesize, ts in history_files:
                safe_from = html.escape(from_user)
                safe_filename = html.escape(filename)
                safe_ts = html.escape(ts)
                display_name = "Я" if from_user == "Director" else safe_from
                link = f'<a href="download://?filename={safe_filename}&from={safe_from}&chat_type=private&to={html.escape(username)}">Скачать</a>'
                combined.append((ts, f"[{safe_ts}] {display_name}: [Файл] {safe_filename} ({filesize} байт) {link}&#8203;"))
            combined.sort(key=lambda x: x[0])
            for _, line in combined:
                self.append_chat_line(chat_widget.chat_display, line)

    def init_ui(self):
        self.setWindowTitle("Asterion - Директор")
        self.setGeometry(100, 100, 1400, 800)
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)
        self.setStyleSheet("""
            QMainWindow { background-color: #2d2d3a; }
            QListWidget {
                background-color: #3d3d4a;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
            }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #4a4a5a; }
            QListWidget::item:selected { background-color: #4a6a8a; }
            QListWidget::item:hover { background-color: #4a4a5a; }
            QTextBrowser {
                background-color: #3d3d4a;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
            }
            QTextBrowser a { color: #4a9a4a; text-decoration: underline; }
            QLineEdit {
                background-color: #3d3d4a;
                border: 1px solid #5a5a6a;
                border-radius: 5px;
                padding: 8px;
                color: #e0e0e0;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #5a7a9a; }
            QPushButton:pressed { background-color: #3a5a7a; }
            QTabWidget::pane { background-color: #3d3d4a; border: none; }
            QTabBar::tab {
                background-color: #4a4a5a;
                color: #a0a0b0;
                padding: 10px 25px;
                border: none;
                font-size: 14px;
            }
            QTabBar::tab:selected { background-color: #5a6a8a; color: white; }
            QTabBar::tab:hover { background-color: #5a5a6a; }
        """)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        self.ip_display = IpDisplayWidget()
        left_layout.addWidget(self.ip_display)
        employees_label = QLabel("Сотрудники")
        employees_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(employees_label)
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.on_user_clicked)
        left_layout.addWidget(self.user_list)
        pending_label = QLabel("Ожидающие")
        pending_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(pending_label)
        self.pending_list = QListWidget()
        self.pending_list.itemClicked.connect(self.on_pending_clicked)
        left_layout.addWidget(self.pending_list)
        main_layout.addWidget(left_panel)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        self.chat_tabs = QTabWidget()
        self.chat_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.general_chat = self.create_chat_widget()
        self.chat_tabs.addTab(self.general_chat, "Общий чат")
        self.screen_tab = QWidget()
        screen_layout = QVBoxLayout()
        self.screen_label = QLabel()
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setStyleSheet("background-color: #1d1d2a; color: #6a6a7a; font-size: 18px;")
        self.screen_label.setText("Выберите сотрудника для просмотра экрана")
        screen_layout.addWidget(self.screen_label)
        btn_layout = QHBoxLayout()
        self.stop_screen_btn = QPushButton("Остановить просмотр")
        self.stop_screen_btn.setEnabled(False)
        self.stop_screen_btn.clicked.connect(self.stop_screen_view)
        btn_layout.addStretch()
        btn_layout.addWidget(self.stop_screen_btn)
        screen_layout.addLayout(btn_layout)
        self.screen_tab.setLayout(screen_layout)
        self.chat_tabs.addTab(self.screen_tab, "Просмотр экрана")
        self.usb_tab = QWidget()
        usb_layout = QVBoxLayout()
        self.usb_display = QTextBrowser()
        self.usb_display.setOpenExternalLinks(False)
        self.usb_display.setStyleSheet("""
            QTextBrowser {
                background-color: #3d3d4a;
                border: 1px solid #4a4a5a;
                border-radius: 6px;
                padding: 12px;
                color: #e0e0e0;
                font-size: 14px;
            }
        """)
        usb_layout.addWidget(self.usb_display)
        self.usb_tab.setLayout(usb_layout)
        self.chat_tabs.addTab(self.usb_tab, "Отслеживание")
        self.stego_tab = StegoTab(self)
        self.chat_tabs.addTab(self.stego_tab, "Стеганография")
        right_layout.addWidget(self.chat_tabs)
        main_layout.addWidget(right_panel)

    def load_general_history(self):
        self.general_chat.chat_display.clear()
        combined = []
        all_messages = db.get_all_general_messages()
        for from_user, to_user, msg, ts in all_messages:
            try:
                decrypted = crypto.decrypt_message(msg)
                safe_from = html.escape(from_user)
                safe_decrypted = html.escape(decrypted)
                safe_ts = html.escape(ts)
                if from_user == "Director":
                    combined.append((ts, f"[{safe_ts}] Я: {safe_decrypted}"))
                else:
                    combined.append((ts, f"[{safe_ts}] {safe_from}: {safe_decrypted}"))
            except:
                safe_from = html.escape(from_user)
                safe_ts = html.escape(ts)
                combined.append((ts, f"[{safe_ts}] {safe_from}: [Зашифровано]"))
        all_files = db.get_general_files()
        for from_user, to_user, filename, filepath, filesize, ts in all_files:
            safe_from = html.escape(from_user)
            safe_filename = html.escape(filename)
            safe_ts = html.escape(ts)
            display_name = "Я" if from_user == "Director" else safe_from
            link = f'<a href="download://?filename={safe_filename}&from={safe_from}&chat_type=general&to=general">Скачать</a>'
            combined.append((ts, f"[{safe_ts}] {display_name}: [Файл] {safe_filename} ({filesize} байт) {link}&#8203;"))
        combined.sort(key=lambda x: x[0])
        for _, line in combined:
            self.append_chat_line(self.general_chat.chat_display, line)

    def create_chat_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        widget.setLayout(layout)
        chat_display = QTextBrowser()
        chat_display.setOpenExternalLinks(False)
        chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #3d3d4a;
                border: 1px solid #4a4a5a;
                border-radius: 6px;
                padding: 12px;
                color: #e0e0e0;
                font-size: 14px;
            }
            QTextBrowser a { color: #4a9a4a; text-decoration: underline; }
        """)
        chat_display.anchorClicked.connect(self.on_link_clicked)
        layout.addWidget(chat_display)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        message_input = QLineEdit()
        message_input.setPlaceholderText("Введите сообщение...")
        message_input.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d4a;
                border: 1px solid #5a5a6a;
                border-radius: 6px;
                padding: 10px 12px;
                color: #e0e0e0;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #4a6a8a; }
        """)
        message_input.returnPressed.connect(lambda: self.send_message(message_input))
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(38, 38)
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #5a7a9a; }
            QPushButton:pressed { background-color: #3a5a7a; }
        """)
        attach_btn.clicked.connect(self.on_attach_clicked)
        send_btn = QPushButton("Тык")
        send_btn.setFixedSize(80, 38)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #5a7a9a; }
            QPushButton:pressed { background-color: #3a5a7a; }
        """)
        send_btn.clicked.connect(lambda: self.send_message(message_input))
        input_layout.addWidget(message_input)
        input_layout.addWidget(attach_btn)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)
        widget.chat_display = chat_display
        widget.message_input = message_input
        return widget

    def on_link_clicked(self, url):
        if self.is_processing_link:
            return
        self.is_processing_link = True
        try:
            if url.scheme() == "download":
                params = {}
                for part in url.query().split('&'):
                    if '=' in part:
                        k, v = part.split('=', 1)
                        params[k] = v
                filename = params.get('filename')
                from_user = params.get('from')
                chat_type = params.get('chat_type')
                to_user = params.get('to')
                if filename and from_user and chat_type and to_user:
                    current_widget = self.chat_tabs.currentWidget()
                    if current_widget:
                        chat_display = current_widget.chat_display
                        saved_html = chat_display.toHtml()
                        scrollbar = chat_display.verticalScrollBar()
                        saved_scroll = scrollbar.value() if scrollbar else None
                        chat_display.setUpdatesEnabled(False)
                        save_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", filename)
                        chat_display.setHtml(saved_html)
                        if saved_scroll is not None and scrollbar:
                            scrollbar.setValue(saved_scroll)
                        chat_display.setUpdatesEnabled(True)
                        if not save_path:
                            return
                        file_info = db.get_file_by_name_and_sender(filename, from_user, to_user, chat_type)
                        if file_info:
                            _, filepath, _ = file_info
                            if os.path.exists(filepath):
                                try:
                                    plain_data = crypto.read_encrypted_file(filepath)
                                    with open(save_path, "wb") as f:
                                        f.write(plain_data)
                                    QMessageBox.information(self, "Успех", f"Файл {filename} сохранён")
                                except Exception as e:
                                    QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
                            else:
                                QMessageBox.critical(self, "Ошибка", "Файл не найден на сервере")
                        else:
                            QMessageBox.critical(self, "Ошибка", "Файл не найден в базе данных")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при скачивании: {str(e)}")
        finally:
            self.is_processing_link = False

    def on_attach_clicked(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл для отправки")
        if not file_path:
            return
        filename = os.path.basename(file_path)
        forbidden_extensions = ['.exe', '.appimage', '.bin', '.msi', '.dmg', '.pkg', '.deb', '.rpm']
        ext = os.path.splitext(filename)[1].lower()
        if ext in forbidden_extensions:
            QMessageBox.warning(self, "Ошибка", "Запрещённый тип файла")
            return
        filesize = os.path.getsize(file_path)
        if filesize > 500 * 1024 * 1024:
            QMessageBox.warning(self, "Ошибка", "Файл превышает 500 МБ")
            return
        current_tab = self.chat_tabs.currentWidget()
        tab_text = self.chat_tabs.tabText(self.chat_tabs.currentIndex())
        if tab_text == "Общий чат":
            chat_type = "general"
            to_user = "general"
        else:
            chat_type = "private"
            to_user = tab_text
        self.send_file(file_path, filename, chat_type, to_user)

    def send_file(self, file_path, filename, chat_type, to_user):
        try:
            safe_filename = f"{int(time.time())}_Director_{filename}"
            filepath = os.path.join("files", safe_filename)
            with open(file_path, "rb") as f:
                plain_data = f.read()
            crypto.write_encrypted_file(filepath, plain_data)
            filesize = os.path.getsize(file_path)
            db.save_file(chat_type, "Director", to_user, filename, filepath, filesize)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            safe_timestamp = html.escape(timestamp)
            safe_filename = html.escape(filename)
            safe_to_user = html.escape(to_user)
            safe_chat_type = html.escape(chat_type)
            link = f'<a href="download://?filename={safe_filename}&from=Director&chat_type={safe_chat_type}&to={safe_to_user}">Скачать</a>'
            if chat_type == "general":
                self.append_chat_line(self.general_chat.chat_display, f"[{safe_timestamp}] Я: [Файл] {safe_filename} ({filesize} байт) {link}&#8203;")
            else:
                if to_user in self.private_chats:
                    self.append_chat_line(self.private_chats[to_user].chat_display, f"[{safe_timestamp}] Я: [Файл] {safe_filename} ({filesize} байт) {link}&#8203;")
            notify_data = {
                'type': 'file_notify',
                'from': 'Director',
                'filename': filename,
                'filesize': filesize,
                'chat_type': chat_type,
                'timestamp': timestamp,
                'to': to_user
            }
            if chat_type == 'general':
                for user, info in self.server_thread.clients.items():
                    try:
                        send_packet(info['socket'], notify_data)
                    except:
                        pass
            else:
                if to_user in self.server_thread.clients:
                    try:
                        send_packet(self.server_thread.clients[to_user]['socket'], notify_data)
                    except:
                        pass
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить файл: {str(e)}")

    def start_server(self):
        self.server_thread = ServerThread(self.server_password)
        self.server_thread.blocker_password_hash = self.blocker_password_hash
        self.server_thread.message_received.connect(self.on_message_received)
        self.server_thread.user_connected.connect(self.on_user_connected)
        self.server_thread.user_disconnected.connect(self.on_user_disconnected)
        self.server_thread.auth_failed.connect(self.on_auth_failed)
        self.server_thread.screen_received.connect(self.on_screen_received)
        self.server_thread.stop_screen_requested.connect(self.on_stop_screen_requested)
        self.server_thread.file_received.connect(self.on_file_received)
        self.server_thread.pending_user_connected.connect(self.on_pending_user_connected)
        self.server_thread.pending_user_removed.connect(self.on_pending_user_removed)
        self.server_thread.usb_event_received.connect(self.on_usb_event)
        self.server_thread.usb_info_response_received.connect(self.on_usb_info_response)
        self.server_thread.start()

    def on_pending_user_connected(self, username):
        self.pending_list.addItem(username)

    def on_pending_user_removed(self, username):
        items = self.pending_list.findItems(username, Qt.MatchFlag.MatchExactly)
        for item in items:
            self.pending_list.takeItem(self.pending_list.row(item))

    def on_pending_clicked(self, item):
        username = item.text()
        menu = QMenu()
        menu.setStyleSheet("background-color: #3d3d4a; color: white; font-size: 13px;")
        approve_action = menu.addAction("Добавить")
        reject_action = menu.addAction("Отклонить")
        t_action = menu.addAction("Трансляция экрана")
        info_action = menu.addAction("Инфо")
        action = menu.exec(QCursor.pos())
        if action == approve_action:
            self.server_thread.approve_user(username)
        elif action == reject_action:
            self.server_thread.reject_user(username)
        elif action == t_action:
            if username in self.server_thread.pending_clients:
                client_socket = self.server_thread.pending_clients[username]['socket']
                try:
                    send_packet(client_socket, {
                        'type': 'request_screen',
                        'from': 'Director'
                    })
                    self.current_screen_user = username
                    self.chat_tabs.setCurrentIndex(self.chat_tabs.indexOf(self.screen_tab))
                    self.screen_label.setText(f"Загрузка экрана {username}...")
                    self.stop_screen_btn.setEnabled(True)
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось отправить запрос: {str(e)}")
        elif action == info_action:
            if username in self.server_thread.pending_clients:
                client_socket = self.server_thread.pending_clients[username]['socket']
                try:
                    send_packet(client_socket, {'type': 'usb_info_request'})
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось запросить информацию: {str(e)}")

    def on_usb_info_response(self, username, devices):
        text = f"Инфо о пользователе: {username}:\n\n"
        if devices:
            for i, dev in enumerate(devices, 1):
                text += f"{dev}\n"
        else:
            text += "Устройства не обнаружены или недоступны."
        QMessageBox.information(self, f"Инфо — {username}", text)

    def on_screen_received(self, username, screen_data):
        if self.current_screen_user == username:
            try:
                from io import BytesIO
                import base64
                from PyQt6.QtGui import QPixmap
                img_bytes = base64.b64decode(screen_data)
                pixmap = QPixmap()
                pixmap.loadFromData(img_bytes, "JPEG")
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        self.screen_label.width() - 20,
                        self.screen_label.height() - 100,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.screen_label.setPixmap(scaled)
                    self.screen_label.setText("")
                else:
                    self.screen_label.setText("Не удалось загрузить изображение")
            except Exception as e:
                self.screen_label.setText(f"Ошибка: {str(e)}")

    def on_stop_screen_requested(self, username):
        if self.current_screen_user == username:
            self.current_screen_user = None
            self.screen_label.setText("Выберите сотрудника для просмотра экрана")
            self.screen_label.setPixmap(QPixmap())
            self.stop_screen_btn.setEnabled(False)

    def stop_screen_view(self):
        if self.current_screen_user and self.current_screen_user in self.server_thread.clients:
            try:
                send_packet(self.server_thread.clients[self.current_screen_user]['socket'], {
                    'type': 'stop_screen',
                    'from': 'Director'
                })
            except:
                pass
        self.current_screen_user = None
        self.screen_label.setText("Выберите сотрудника для просмотра экрана")
        self.screen_label.setPixmap(QPixmap())
        self.stop_screen_btn.setEnabled(False)

    def on_auth_failed(self, username):
        pass

    def on_user_connected(self, username):
        self.user_list.addItem(username)
        self.on_pending_user_removed(username)
        if username not in self.private_chats:
            chat_widget = self.create_chat_widget()
            self.chat_tabs.addTab(chat_widget, username)
            self.private_chats[username] = chat_widget
            history_messages = db.get_private_messages("Director", username)
            history_files = db.get_private_files("Director", username)
            combined = []
            for from_user, to_user, msg, ts in history_messages:
                try:
                    decrypted = crypto.decrypt_message(msg)
                    safe_from = html.escape(from_user)
                    safe_decrypted = html.escape(decrypted)
                    safe_ts = html.escape(ts)
                    display_name = "Я" if from_user == "Director" else safe_from
                    combined.append((ts, f"[{safe_ts}] {display_name}: {safe_decrypted}"))
                except:
                    safe_from = html.escape(from_user)
                    safe_ts = html.escape(ts)
                    combined.append((ts, f"[{safe_ts}] {safe_from}: [Зашифровано]"))
            for from_user, to_user, filename, filepath, filesize, ts in history_files:
                safe_from = html.escape(from_user)
                safe_filename = html.escape(filename)
                safe_ts = html.escape(ts)
                display_name = "Я" if from_user == "Director" else safe_from
                link = f'<a href="download://?filename={safe_filename}&from={safe_from}&chat_type=private&to={html.escape(username)}">Скачать</a>'
                combined.append((ts, f"[{safe_ts}] {display_name}: [Файл] {safe_filename} ({filesize} байт) {link}&#8203;"))
            combined.sort(key=lambda x: x[0])
            for _, line in combined:
                self.append_chat_line(chat_widget.chat_display, line)
        self.server_thread.send_history(username)

    def on_user_disconnected(self, username):
        items = self.user_list.findItems(username, Qt.MatchFlag.MatchExactly)
        for item in items:
            self.user_list.takeItem(self.user_list.row(item))
        if self.current_screen_user == username:
            self.current_screen_user = None
            self.screen_label.setText("Выберите сотрудника для просмотра экрана")
            self.screen_label.setPixmap(QPixmap())
            self.stop_screen_btn.setEnabled(False)

    def on_file_received(self, from_user, to_user, filename, chat_type, filesize, timestamp):
        play_alert_sound()
        safe_from = html.escape(from_user)
        safe_filename = html.escape(filename)
        safe_timestamp = html.escape(timestamp)
        safe_to = html.escape(to_user)
        safe_chat_type = html.escape(chat_type)
        link = f'<a href="download://?filename={safe_filename}&from={safe_from}&chat_type={safe_chat_type}&to={safe_to}">Скачать</a>&#8203;'
        line = f"[{safe_timestamp}] {safe_from}: [Файл] {safe_filename} ({filesize} байт) {link}"
        if chat_type == "general":
            self.append_chat_line(self.general_chat.chat_display, line)
        else:
            if from_user in self.private_chats:
                self.append_chat_line(self.private_chats[from_user].chat_display, line)
            elif to_user in self.private_chats:
                self.append_chat_line(self.private_chats[to_user].chat_display, line)

    def on_message_received(self, from_user, message, to_user, chat_type):
        play_alert_sound()
        safe_from_user = html.escape(from_user)
        if from_user == "Director":
            display_message = message
        else:
            try:
                display_message = crypto.decrypt_message(message)
            except:
                display_message = "[Decryption error]"
        safe_display_message = html.escape(display_message)
        timestamp = datetime.now().strftime('%H:%M:%S')
        safe_timestamp = html.escape(timestamp)
        line = f"[{safe_timestamp}] {safe_from_user}: {safe_display_message}"
        if chat_type == "general":
            self.append_chat_line(
                self.general_chat.chat_display,
                line
            )
        else:
            if from_user in self.private_chats:
                self.append_chat_line(
                    self.private_chats[from_user].chat_display,
                    line
                )

    def send_message(self, input_widget):
        message = input_widget.text().strip()
        if not message:
            return
        current_tab = self.chat_tabs.currentWidget()
        tab_text = self.chat_tabs.tabText(self.chat_tabs.currentIndex())
        timestamp = datetime.now().strftime('%H:%M:%S')
        safe_timestamp = html.escape(timestamp)
        safe_message = html.escape(message)
        if tab_text == "Общий чат":
            encrypted = crypto.encrypt_message(message)
            db.save_message("general", "Director", "general", encrypted)
            self.append_chat_line(self.general_chat.chat_display, f"[{safe_timestamp}] Я: {safe_message}")
            for user, info in self.server_thread.clients.items():
                try:
                    send_packet(info['socket'], {
                        'type': 'message',
                        'from': 'Director',
                        'message': self.server_thread.transport.encrypt_text(message),
                        'to': 'general'
                    })
                except:
                    pass
        else:
            to_user = tab_text
            if to_user in self.private_chats:
                encrypted = crypto.encrypt_message(message)
                db.save_message("private", "Director", to_user, encrypted)
                self.append_chat_line(
                    self.private_chats[to_user].chat_display,
                    f"[{safe_timestamp}] Я: {safe_message}")
                if to_user in self.server_thread.clients:
                    try:
                        send_packet(self.server_thread.clients[to_user]['socket'], {
                            'type': 'message',
                            'from': 'Director',
                            'message': self.server_thread.transport.encrypt_text(message),
                            'to': to_user
                        })
                    except:
                        pass
        input_widget.clear()

    def on_user_clicked(self, item):
        username = item.text()
        menu = QMenu()
        menu.setStyleSheet("background-color: #3d3d4a; color: white; font-size: 13px;")
        view_screen = menu.addAction("Просмотр экрана")
        send_notification = menu.addAction("Отправить уведомление")
        block_access = menu.addAction("Заблокировать доступ")
        action = menu.exec(QCursor.pos())
        if action == view_screen:
            if username in self.server_thread.clients:
                try:
                    send_packet(self.server_thread.clients[username]['socket'], {
                        'type': 'request_screen',
                        'from': 'Director'
                    })
                    self.current_screen_user = username
                    self.chat_tabs.setCurrentIndex(self.chat_tabs.indexOf(self.screen_tab))
                    self.screen_label.setText(f"Загрузка экрана {username}...")
                    self.stop_screen_btn.setEnabled(True)
                except:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось отправить запрос {username}")
            else:
                QMessageBox.warning(self, "Ошибка", f"Пользователь {username} не в сети")
        elif action == send_notification:
            dialog = QDialog(self)
            dialog.setWindowTitle("Отправить уведомление")
            dialog.setFixedSize(450, 250)
            dialog.setStyleSheet("""
                QDialog { background-color: #3d3d4a; }
                QLabel { color: white; font-size: 14px; }
                QTextEdit {
                    background-color: #4a4a5a;
                    border: 1px solid #5a5a6a;
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 14px;
                    padding: 10px;
                }
                QTextEdit:focus { border: 1px solid #4a6a8a; }
                QPushButton {
                    background-color: #4a6a8a;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #5a7a9a; }
            """)
            layout = QVBoxLayout()
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(12)
            label = QLabel(f"Уведомление для {username}:")
            layout.addWidget(label)
            text_input = QTextEdit()
            text_input.setMinimumHeight(80)
            layout.addWidget(text_input)
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(10)
            send_btn = QPushButton("Отправить")
            send_btn.setMinimumHeight(40)
            cancel_btn = QPushButton("Отмена")
            cancel_btn.setMinimumHeight(40)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #5a4a4a;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #6a5a5a; }
            """)
            btn_layout.addWidget(send_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            dialog.setLayout(layout)
            send_btn.clicked.connect(lambda: self.send_notification_action(dialog, username, text_input.toPlainText()))
            cancel_btn.clicked.connect(dialog.reject)
            dialog.exec()
        elif action == block_access:
            if username in self.server_thread.clients:
                try:
                    send_packet(self.server_thread.clients[username]['socket'], {
                        'type': 'block_access',
                        'to': username
                    })
                except:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось отправить команду блокировки {username}")
            else:
                QMessageBox.warning(self, "Ошибка", f"Пользователь {username} не в сети")

    def send_notification_action(self, dialog, username, message):
        if not message.strip():
            QMessageBox.warning(self, "Ошибка", "Введите текст уведомления")
            return
        if self.server_thread.send_notification(username, message):
            dialog.accept()
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось отправить уведомление {username}")

    def on_usb_event(self, username, timestamp, message):
        play_alert_sound()
        self.append_chat_line(self.usb_display, f"{username}, {timestamp}: {message}")

    def closeEvent(self, event):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = app.font()
    font.setFamily("Arial")
    font.setPointSize(10)
    app.setFont(font)

    password_dialog = ServerPasswordDialog()
    while True:
        if password_dialog.exec() == QDialog.DialogCode.Accepted:
            password, error = password_dialog.get_password()
            if password:
                break
            else:
                QMessageBox.warning(None, "Ошибка", error)
        else:
            sys.exit(0)

    blocker_dialog = BlockerPasswordDialog()
    while True:
        if blocker_dialog.exec() == QDialog.DialogCode.Accepted:
            blocker_password, error = blocker_dialog.get_password()
            if blocker_password:
                break
            else:
                QMessageBox.warning(None, "Ошибка", error)
        else:
            sys.exit(0)

    login_password = password[:len(password) // 2]
    global crypto
    try:
        crypto = CryptoManager(password)
    except ValueError as e:
        QMessageBox.critical(None, "Ошибка", str(e))
        sys.exit(1)

    QMessageBox.information(None, "Пароль для входа сотрудников",
                             f"Сотрудники должны вводить для входа: {login_password}")

    window = MainWindow(login_password, hash_password(blocker_password))
    window.show()
    sys.exit(app.exec())

main()