import sys
import json
import threading
import hashlib
import socket
import ssl
import time
import base64
import os
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import mss
import numpy as np
import cv2
from crypto import TransportCipher
import pygame
from io import BytesIO

SOUND_ALERT_MP3 = base64.b64decode("""SUQzAwAAAABIIlREQVQAAAAFAAAAMTQwM1RJTUUAAAAFAAAAMTc1NFBSSVYAABvoAABYTVAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS41LWMwMjEgNzkuMTU1MjQxLCAyMDEzLzExLzI1LTIxOjEwOjQwICAgICAgICAiPgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iCiAgICB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIgogICAgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiCiAgICB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iCiAgICB4bWxuczp4bXBETT0iaHR0cDovL25zLmFkb2JlLmNvbS94bXAvMS4wL0R5bmFtaWNNZWRpYS8iCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpiZXh0PSJodHRwOi8vbnMuYWRvYmUuY29tL2J3Zi9iZXh0LzEuMC8iCiAgIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MmYxZjVkMGUtYzIyMS00MzI0LWEwNGUtMTc0OTk3YTRjZTRlIgogICB4bXBNTTpEb2N1bWVudElEPSIwNGRhNTY4Yy1kOTJiLTFiZjMtM2VhMS02YjA0MDAwMDAwNDkiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpiNmFkYmNkMS1hNzBmLTQ5NjUtYWNjMS00ODg2OWEwMDIxM2QiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMTQtMDMtMTRUMTc6NTQ6NTgtMDQ6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDE0LTAzLTE0VDE3OjU0OjU4LTA0OjAwIgogICB4bXA6Q3JlYXRlRGF0ZT0iMjAxNC0wMy0xNFQxNzo1NDoyOC0wNDowMCIKICAgeG1wRE06YXVkaW9TYW1wbGVSYXRlPSI0NDEwMCIKICAgeG1wRE06YXVkaW9TYW1wbGVUeXBlPSIxNkludCIKICAgeG1wRE06YXVkaW9DaGFubmVsVHlwZT0iU3RlcmVvIgogICB4bXBETTpzdGFydFRpbWVTY2FsZT0iMzAwMDAiCiAgIHhtcERNOnN0YXJ0VGltZVNhbXBsZVNpemU9IjEwMDEiCiAgIHhtcERNOnBhcnRPZkNvbXBpbGF0aW9uPSJmYWxzZSIKICAgZGM6Zm9ybWF0PSJNUDMiCiAgIGJleHQ6ZGVzY3JpcHRpb249Ik1VTFRJTUVESUEgQlVUVE9OIFRPTkFMIDAzIgogICBiZXh0Om9yaWdpbmF0b3I9IkFkb2JlIFN5c3RlbXMgSW5jIgogICBiZXh0Om9yaWdpbmF0aW9uRGF0ZT0iMjAxNC0wMy0wNSIKICAgYmV4dDpvcmlnaW5hdGlvblRpbWU9IjE5OjQ2OjExIgogICBiZXh0OnRpbWVSZWZlcmVuY2U9IjAiCiAgIGJleHQ6dmVyc2lvbj0iMSI+CiAgIDx4bXBNTTpIaXN0b3J5PgogICAgPHJkZjpTZXE+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSIyZWZmN2MyMi1lMzMyLTMwNTMtNTFiYS0xZGVlMDAwMDAwNzYiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMTRUMTc6NTQ6NTgtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9ImZkY2QyZDZhLWJmMmQtNDFkNS0wOTk0LWIxZTUwMDAwMDA3NiIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0xMlQxMzo1NS0wNDowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0iOTc3M2Q2ZDgtNTg0Mi00ZjdhLTBmYTAtZWIxZTAwMDAwMDc2IgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTA1VDE5OjQ2OjExLTA1OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOkJBQ0Q2NkE3OEYyMDY4MTE5MTA5QjNCMUQxRkI1RDE0IgogICAgICBzdEV2dDp3aGVuPSIyMDEzLTA0LTMwVDExOjAyOjM4LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIDUuNS4wIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvbWV0YWRhdGE7L2NvbnRlbnQiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6NDFDQkI4N0I5MTIwNjgxMTkxMDlCM0IxRDFGQjVEMTQiCiAgICAgIHN0RXZ0OndoZW49IjIwMTMtMDQtMzBUMTE6MTU6NDgtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgNS41LjAiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ibW9kaWZpZWQiCiAgICAgIHN0RXZ0OnBhcmFtZXRlcnM9InVua25vd24gbW9kaWZpY2F0aW9ucyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0iNTQxNDk3MzMtYjFhMC1mZDFkLTMwYWItZmUxOTAwMDAwMDc2IgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTA1VDE4OjU1OjI5LTA1OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU5ZDUzY2VjLTc0NjQtNGE3ZC04N2ZjLWMwYzM5MjYyYmYyNSIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0wNVQxOTo0NjoxMS0wNTowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDplNGIxZWE1MC02ZGU0LTRkZGEtOTZkYy0xZGZhMDFlMzA1ZjEiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMDVUMTk6NDY6MTEtMDU6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii9tZXRhZGF0YSIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDowMGY5ZDIyMi03ZmM3LTQxZTQtYTc3ZS02MTFmMGUzM2JiN2EiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMTJUMTM6NTUtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZDBmZGRjMDUtM2M3NC00MzAwLTlhYjItMzU2YTMwM2VmNjEwIgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTEyVDEzOjU1LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvbWV0YWRhdGEiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6MjEwYWI2NTAtNjkwZS00MzllLWI1NzktOWNkY2I1NjU3Y2JiIgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTE0VDE3OjU0OjU4LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjJmMWY1ZDBlLWMyMjEtNDMyNC1hMDRlLTE3NDk5N2E0Y2U0ZSIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0xNFQxNzo1NDo1OC0wNDowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iL21ldGFkYXRhIi8+CiAgICA8L3JkZjpTZXE+CiAgIDwveG1wTU06SGlzdG9yeT4KICAgPHhtcE1NOkRlcml2ZWRGcm9tCiAgICBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOmQwZmRkYzA1LTNjNzQtNDMwMC05YWIyLTM1NmEzMDNlZjYxMCIKICAgIHN0UmVmOmRvY3VtZW50SUQ9Ijc3ZjgyMzkxLWYyNjYtNzRlZS0wMTExLWFhZWUwMDAwMDA0OSIKICAgIHN0UmVmOm9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDoyZTEzYzBhNC00ZDFjLTRmNDQtYjcwYi1lZDQyYmI5OTBhNTYiLz4KICAgPHhtcERNOnN0YXJ0VGltZWNvZGUKICAgIHhtcERNOnRpbWVGb3JtYXQ9IjI5OTdEcm9wVGltZWNvZGUiCiAgICB4bXBETTp0aW1lVmFsdWU9IjAwOzAwOzAwOzAwIi8+CiAgIDx4bXBETTphbHRUaW1lY29kZQogICAgeG1wRE06dGltZVZhbHVlPSIwMDswMDswMDswMCIKICAgIHhtcERNOnRpbWVGb3JtYXQ9IjI5OTdEcm9wVGltZWNvZGUiLz4KICAgPHhtcERNOmR1cmF0aW9uCiAgICB4bXBETTp2YWx1ZT0iMyIKICAgIHhtcERNOnNjYWxlPSIxMDAxLzMwMDAwIi8+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz4AVEJQTQAAAAcAAAAxMjEuOTdUWUVSAAAABQAAADIwMjFUSVQyAAAABAAAAHNtcwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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///////////////////////////////////7cGCQAAIrF9Brb3pMN0SqHWUtS8dATyOM7ecosInksY2g5P/////////////////////////////8gqMgAGF86WCXMNFAEwE10ke2e5D/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+3BgqQACngfGoHrIqhPg+MQHOBVAAAEuAAAAIAAAJcAAAAT///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////twQP+ACKgAS4AAAAgAAAlwAAABAAABLgAAACAAACXAAAAE/////////////////////////////////////////////////////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/7cED/gAioAEuAAAAIAAAJcAAAAQAAAS4AAAAgAAAlwAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABUQUcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAyMDE0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==""".strip())

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
    def __init__(self):
        self.buffer = b''
    def feed(self, chunk: bytes):
        self.buffer += chunk
    def pop_packets(self):
        packets = []
        while True:
            if len(self.buffer) < 4:
                break
            length = int.from_bytes(self.buffer[:4], byteorder='big')
            if len(self.buffer) < 4 + length:
                break
            raw = self.buffer[4:4 + length]
            self.buffer = self.buffer[4 + length:]
            try:
                packets.append(json.loads(raw.decode('utf-8')))
            except json.JSONDecodeError:
                pass
        return packets

class ScreenStream(QThread):
    def __init__(self, sock, transport, target='Director', fps=30):
        super().__init__()
        self.sock = sock
        self.transport = transport
        self.target = target
        self.running = False
        self.sct = mss.MSS()
        self.interval = 1.0 / fps

    def start_stream(self):
        if not self.running:
            self.running = True
            self.start()

    def stop_stream(self):
        self.running = False
        self.wait()

    def run(self):
        while self.running:
            try:
                monitor = self.sct.monitors[1]
                frame = self.sct.grab(monitor)
                img = np.array(frame)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                img_resized = cv2.resize(img, (800, 600), interpolation=cv2.INTER_LINEAR)
                ret, jpeg = cv2.imencode('.jpg', img_resized, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if not ret:
                    time.sleep(self.interval)
                    continue
                img_str = base64.b64encode(jpeg.tobytes()).decode()
                if len(img_str) < 300000:
                    packet = {
                        'type': 'screen',
                        'to': self.target,
                        'data': self.transport.encrypt_text(img_str)
                    }
                    send_packet(self.sock, packet)
                time.sleep(self.interval)
            except:
                time.sleep(self.interval)

class AuthThread(QThread):
    auth_success = pyqtSignal(object, str, str, object)
    auth_failed = pyqtSignal(str)
    connection_error = pyqtSignal(str)
    pending_status = pyqtSignal()
    screen_request = pyqtSignal(object)

    def __init__(self, server_ip, username, password, port=5555):
        super().__init__()
        if ':' in server_ip:
            parts = server_ip.split(':')
            server_ip = parts[0]
            try:
                port = int(parts[1])
            except:
                port = 5555
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.port = port
        self.screen_stream = None
        self.transport = None

    def run(self):
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            ssl_sock = context.wrap_socket(sock, server_hostname=self.server_ip)
            try:
                ssl_sock.connect((self.server_ip, self.port))
            except socket.error as e:
                self.connection_error.emit(f"Не удалось подключиться к {self.server_ip}:{self.port} - {str(e)}")
                return
            try:
                send_packet(ssl_sock, {
                    'username': self.username,
                    'password': hashlib.sha256(self.password.encode()).hexdigest()
                })
            except socket.error as e:
                self.connection_error.emit(f"Не удалось отправить данные авторизации - {str(e)}")
                ssl_sock.close()
                return
            self.transport = TransportCipher(self.password)
            reader = PacketReader()
            while True:
                try:
                    chunk = ssl_sock.recv(4096)
                    if not chunk:
                        break
                    reader.feed(chunk)
                    for pkt in reader.pop_packets():
                        ptype = pkt.get('type')
                        if ptype == 'approved':
                            self.auth_success.emit(ssl_sock, self.username, self.password, self.screen_stream)
                            return
                        elif ptype == 'rejected':
                            if self.screen_stream:
                                self.screen_stream.stop_stream()
                            ssl_sock.close()
                            self.auth_failed.emit("Заявка отклонена администратором")
                            return
                        elif ptype == 'request_screen':
                            if self.screen_stream is None:
                                self.screen_stream = ScreenStream(ssl_sock, self.transport)
                            self.screen_stream.start_stream()
                            self.screen_request.emit(self.screen_stream)
                        elif ptype == 'stop_screen':
                            if self.screen_stream:
                                self.screen_stream.stop_stream()
                except socket.timeout:
                    continue
                except Exception as e:
                    self.auth_failed.emit(f"Ошибка авторизации: {str(e)}")
                    ssl_sock.close()
                    return
        except Exception as e:
            self.connection_error.emit(f"Ошибка подключения: {str(e)}")

class ClientThread(QThread):
    message_received = pyqtSignal(str, str, str)
    notification_received = pyqtSignal(str)
    screen_requested = pyqtSignal()
    stop_screen_requested = pyqtSignal()
    history_received = pyqtSignal(list)
    file_notify_received = pyqtSignal(str, str, str, int, str)
    file_download_chunk_received = pyqtSignal(str, int, int, bytes)
    connection_error = pyqtSignal(str)

    def __init__(self, socket, username, password):
        super().__init__()
        self.socket = socket
        self.username = username
        self.password = password
        self.running = True
        self.download_buffers = {}
        self.reader = PacketReader()
        self.transport = TransportCipher(password)
        self.screen_stream = None

    def set_screen_stream(self, stream):
        if self.screen_stream:
            self.screen_stream.stop_stream()
        self.screen_stream = stream
        if stream:
            stream.sock = self.socket
            stream.transport = self.transport
            stream.start_stream()

    def run(self):
        try:
            while self.running:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    self.reader.feed(data)
                    for packet in self.reader.pop_packets():
                        packet_type = packet.get('type')
                        if packet_type == 'message':
                            from_user = packet.get('from', 'Неизвестный')
                            message = self.transport.decrypt_text(packet.get('message', ''))
                            to_user = packet.get('to', 'general')
                            self.message_received.emit(from_user, message, to_user)
                        elif packet_type == 'notification':
                            message = self.transport.decrypt_text(packet.get('message', ''))
                            self.notification_received.emit(message)
                        elif packet_type == 'request_screen':
                            self.screen_requested.emit()
                        elif packet_type == 'stop_screen':
                            self.stop_screen_requested.emit()
                        elif packet_type == 'history':
                            messages = packet.get('messages', [])
                            for msg in messages:
                                if msg.get('type') == 'message':
                                    msg['message'] = self.transport.decrypt_text(msg.get('message', ''))
                            self.history_received.emit(messages)
                        elif packet_type == 'file_notify':
                            from_user = packet.get('from')
                            filename = packet.get('filename')
                            chat_type = packet.get('chat_type')
                            filesize = packet.get('filesize')
                            timestamp = packet.get('timestamp')
                            self.file_notify_received.emit(from_user, filename, chat_type, filesize, timestamp)
                        elif packet_type == 'file_download_chunk':
                            file_id = packet.get('file_id')
                            chunk_index = packet.get('chunk_index')
                            total_chunks = packet.get('total_chunks')
                            data_token = packet.get('data')
                            chunk_data = self.transport.decrypt_bytes(data_token)
                            self.file_download_chunk_received.emit(file_id, chunk_index, total_chunks, chunk_data)
                except socket.timeout:
                    continue
                except socket.error as e:
                    self.connection_error.emit(f"Ошибка сокета: {str(e)}")
                    break
                except Exception as e:
                    self.connection_error.emit(f"Ошибка: {str(e)}")
                    break
        except Exception as e:
            self.connection_error.emit(f"Ошибка: {str(e)}")
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass

    def send_message(self, to_user, message):
        if self.socket:
            try:
                packet = {
                    'type': 'message',
                    'to': to_user,
                    'message': self.transport.encrypt_text(message)
                }
                send_packet(self.socket, packet)
                return True
            except:
                return False
        return False

    def send_screen(self, to_user, screen_data):
        if self.socket:
            try:
                packet = {
                    'type': 'screen',
                    'to': to_user,
                    'data': self.transport.encrypt_text(screen_data)
                }
                send_packet(self.socket, packet)
                return True
            except:
                return False
        return False

    def request_file(self, filename, from_user, chat_type, to_user):
        if self.socket:
            try:
                packet = {
                    'type': 'file_request',
                    'filename': filename,
                    'from_user': from_user,
                    'chat_type': chat_type,
                    'to_user': to_user
                }
                send_packet(self.socket, packet)
                return True
            except:
                return False
        return False

    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.server_ip = ""
        self.username = ""
        self.password = ""
        self.auth_thread = None
        self.pending = False
        self.socket = None
        self.screen_stream = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Asterion - Подключение")
        self.setFixedSize(450, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d3a;
            }
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: 500;
            }
            QLineEdit {
                background-color: #3d3d4a;
                border: 1px solid #5a5a6a;
                border-radius: 6px;
                padding: 10px 12px;
                color: #e0e0e0;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 1px solid #4a6a8a;
            }
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                color: white;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #5a7a9a;
            }
            QPushButton:pressed {
                background-color: #3a5a7a;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        title_label = QLabel("Asterion")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4a9a4a; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        ip_label = QLabel("IP-адрес сервера:")
        layout.addWidget(ip_label)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        self.ip_input.setMinimumHeight(40)
        layout.addWidget(self.ip_input)
        name_label = QLabel("Ваше имя:")
        layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Иванов")
        self.name_input.setMinimumHeight(40)
        layout.addWidget(self.name_input)
        password_label = QLabel("Пароль сервера:")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)
        layout.addSpacing(10)
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setMinimumHeight(45)
        self.connect_btn.clicked.connect(self.on_connect)
        layout.addWidget(self.connect_btn)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def on_connect(self):
        self.server_ip = self.ip_input.text().strip()
        self.username = self.name_input.text().strip()
        self.password = self.password_input.text().strip()
        if not self.server_ip or not self.username or not self.password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Подключение...")
        self.status_label.hide()
        self.auth_thread = AuthThread(self.server_ip, self.username, self.password)
        self.auth_thread.auth_success.connect(self.on_auth_success)
        self.auth_thread.auth_failed.connect(self.on_auth_failed)
        self.auth_thread.connection_error.connect(self.on_connection_error)
        self.auth_thread.pending_status.connect(self.on_pending)
        self.auth_thread.screen_request.connect(self.on_screen_request)
        self.auth_thread.start()

    def on_screen_request(self, stream):
        self.screen_stream = stream

    def on_pending(self):
        self.pending = True
        self.connect_btn.setText("Ожидание одобрения...")
        self.status_label.setText("Ожидание одобрения администратором...")
        self.status_label.show()

    def on_auth_success(self, sock, username, password, screen_stream):
        self.socket = sock
        self.username = username
        self.password = password
        self.screen_stream = screen_stream
        self.accept()

    def on_auth_failed(self, error):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Подключиться")
        self.status_label.hide()
        QMessageBox.critical(self, "Ошибка авторизации", f"{error}")
        sys.exit(1)

    def on_connection_error(self, error):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Подключиться")
        self.status_label.hide()
        QMessageBox.critical(self, "Ошибка подключения", f"{error}")
        sys.exit(1)

    def get_socket_and_credentials(self):
        return self.socket, self.username, self.password, self.screen_stream

class MainWindow(QMainWindow):
    def __init__(self, sock, username, password, screen_stream=None):
        super().__init__()
        self.sock = sock
        self.username = username
        self.password = password
        self.client_thread = None
        self.screen_timer = None
        self.screen_active = False
        self.sct = mss.MSS()
        self.download_buffers = {}
        self.is_processing_download = False
        self.screen_stream = screen_stream
        self.init_ui()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self.start_client_thread()

    def init_ui(self):
        self.setWindowTitle(f"Asterion - {self.username}")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d3a;
            }
            QTextBrowser {
                background-color: #3d3d4a;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
            }
            QTextBrowser a {
                color: #4a9a4a;
                text-decoration: underline;
            }
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
            QPushButton:hover {
                background-color: #5a7a9a;
            }
            QPushButton:pressed {
                background-color: #3a5a7a;
            }
            QTabWidget::pane {
                background-color: #3d3d4a;
                border: none;
            }
            QTabBar::tab {
                background-color: #4a4a5a;
                color: #a0a0b0;
                padding: 10px 25px;
                border: none;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #5a6a8a;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5a5a6a;
            }
        """)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        central_widget.setLayout(layout)
        self.chat_tabs = QTabWidget()
        self.chat_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.general_chat = self.create_chat_widget()
        self.chat_tabs.addTab(self.general_chat, "Общий чат")
        self.private_chat = self.create_chat_widget()
        self.chat_tabs.addTab(self.private_chat, "Чат с Директором")
        layout.addWidget(self.chat_tabs)

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
            QTextBrowser a {
                color: #4a9a4a;
                text-decoration: underline;
            }
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
            QLineEdit:focus {
                border: 1px solid #4a6a8a;
            }
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
            QPushButton:hover {
                background-color: #5a7a9a;
            }
            QPushButton:pressed {
                background-color: #3a5a7a;
            }
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
            QPushButton:hover {
                background-color: #5a7a9a;
            }
            QPushButton:pressed {
                background-color: #3a5a7a;
            }
        """)
        send_btn.clicked.connect(lambda: self.send_message(message_input))
        input_layout.addWidget(message_input)
        input_layout.addWidget(attach_btn)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)
        widget.chat_display = chat_display
        widget.message_input = message_input
        return widget

    def append_chat_line(self, chat_display, line):
        chat_display.append(line)
        cursor = chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.setCharFormat(QTextCharFormat())
        chat_display.setTextCursor(cursor)

    def on_link_clicked(self, url):
        if self.is_processing_download:
            return
        self.is_processing_download = True
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
                        if saved_scroll is not None:
                            scrollbar.setValue(saved_scroll)
                        chat_display.setUpdatesEnabled(True)
                        if not save_path:
                            return
                        self.download_file(filename, from_user, chat_type, to_user, save_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при скачивании: {str(e)}")
        finally:
            self.is_processing_download = False

    def download_file(self, filename, from_user, chat_type, to_user, save_path):
        self.download_buffers[save_path] = {
            'file_id': None,
            'chunks': {},
            'total_chunks': 0,
            'filename': filename
        }
        self.client_thread.request_file(filename, from_user, chat_type, to_user)
        self.download_progress = QProgressDialog(f"Скачивание {filename}...", "Отмена", 0, 100, self)
        self.download_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.download_progress.setMinimumDuration(0)
        self.download_progress.setValue(0)
        self.download_progress.canceled.connect(lambda: self.cancel_download(save_path))
        self.download_progress.show()

    def cancel_download(self, save_path):
        if save_path in self.download_buffers:
            del self.download_buffers[save_path]
        self.download_progress.close()

    def on_file_download_chunk(self, file_id, chunk_index, total_chunks, chunk_data):
        for save_path, info in self.download_buffers.items():
            if info['file_id'] is None:
                info['file_id'] = file_id
                info['total_chunks'] = total_chunks
            if info['file_id'] == file_id:
                info['chunks'][chunk_index] = chunk_data
                progress = int((len(info['chunks']) / total_chunks) * 100)
                self.download_progress.setValue(progress)
                if len(info['chunks']) == total_chunks:
                    self.download_progress.setValue(100)
                    try:
                        with open(save_path, "wb") as f:
                            for i in range(total_chunks):
                                f.write(info['chunks'][i])
                        QMessageBox.information(self, "Успех", f"Файл {info['filename']} сохранён")
                    except Exception as e:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
                    self.download_progress.close()
                    del self.download_buffers[save_path]

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
        chunk_size = 1024 * 1024
        filesize = os.path.getsize(file_path)
        total_chunks = (filesize + chunk_size - 1) // chunk_size
        file_id = f"{int(time.time())}_{self.username}_{filename}"
        progress = QProgressDialog(f"Отправка {filename}...", "Отмена", 0, total_chunks, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        try:
            with open(file_path, "rb") as f:
                for i in range(total_chunks):
                    if progress.wasCanceled():
                        break
                    data = f.read(chunk_size)
                    data_token = self.client_thread.transport.encrypt_bytes(data)
                    packet = {
                        'type': 'file_chunk',
                        'file_id': file_id,
                        'chunk_index': i,
                        'data': data_token
                    }
                    if i == 0:
                        start_packet = {
                            'type': 'file_start',
                            'file_id': file_id,
                            'filename': filename,
                            'filesize': filesize,
                            'total_chunks': total_chunks,
                            'chat_type': chat_type,
                            'to': to_user
                        }
                        send_packet(self.client_thread.socket, start_packet)
                    send_packet(self.client_thread.socket, packet)
                    progress.setValue(i + 1)
                    QApplication.processEvents()
                if not progress.wasCanceled():
                    end_packet = {
                        'type': 'file_end',
                        'file_id': file_id,
                        'filename': filename,
                        'chat_type': chat_type,
                        'to': to_user
                    }
                    send_packet(self.client_thread.socket, end_packet)
                else:
                    QMessageBox.information(self, "Отмена", "Отправка файла отменена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить файл: {str(e)}")
        progress.close()

    def start_client_thread(self):
        self.client_thread = ClientThread(self.sock, self.username, self.password)
        if self.screen_stream:
            self.client_thread.set_screen_stream(self.screen_stream)
        self.client_thread.message_received.connect(self.on_message_received)
        self.client_thread.notification_received.connect(self.on_notification_received)
        self.client_thread.screen_requested.connect(self.on_screen_requested)
        self.client_thread.stop_screen_requested.connect(self.on_stop_screen_requested)
        self.client_thread.history_received.connect(self.on_history_received)
        self.client_thread.file_notify_received.connect(self.on_file_notify_received)
        self.client_thread.file_download_chunk_received.connect(self.on_file_download_chunk)
        self.client_thread.connection_error.connect(self.on_connection_error)
        self.client_thread.start()

    def on_file_notify_received(self, from_user, filename, chat_type, filesize, timestamp):
        play_alert_sound()
        link = f'<a href="download://?filename={filename}&from={from_user}&chat_type={chat_type}&to={self.username}">Скачать</a>&#8203;'
        msg = f"[{timestamp}] {from_user}: [Файл] {filename} ({filesize} байт) {link}"
        if chat_type == "general":
            self.append_chat_line(self.general_chat.chat_display, msg)
        else:
            self.append_chat_line(self.private_chat.chat_display, msg)

    def on_connection_error(self, error):
        self.close()
        QMessageBox.critical(None, "Ошибка подключения", f"Соединение потеряно: {error}")
        QApplication.quit()

    def on_history_received(self, messages):
        for msg in messages:
            if msg.get('type') == 'message':
                from_user = msg.get('from', 'Неизвестный')
                to_user = msg.get('to', 'general')
                message = msg.get('message', '')
                timestamp = msg.get('timestamp', '')
                chat_type = msg.get('chat_type', 'general')
                if chat_type == 'general':
                    self.append_chat_line(self.general_chat.chat_display, f"[{timestamp}] {from_user}: {message}")
                else:
                    self.append_chat_line(self.private_chat.chat_display, f"[{timestamp}] {from_user}: {message}")
            elif msg.get('type') == 'file':
                from_user = msg.get('from', 'Неизвестный')
                filename = msg.get('filename', '')
                filesize = msg.get('filesize', 0)
                timestamp = msg.get('timestamp', '')
                chat_type = msg.get('chat_type', 'general')
                link = f'<a href="download://?filename={filename}&from={from_user}&chat_type={chat_type}&to={self.username}">Скачать</a>&#8203;'
                line = f"[{timestamp}] {from_user}: [Файл] {filename} ({filesize} байт) {link}"
                if chat_type == 'general':
                    self.append_chat_line(self.general_chat.chat_display, line)
                else:
                    self.append_chat_line(self.private_chat.chat_display, line)

    def on_message_received(self, from_user, message, to_user):
        play_alert_sound()
        if to_user == "general":
            self.append_chat_line(self.general_chat.chat_display, f"[{datetime.now().strftime('%H:%M:%S')}] {from_user}: {message}")
        else:
            self.append_chat_line(self.private_chat.chat_display, f"[{datetime.now().strftime('%H:%M:%S')}] {from_user}: {message}")

    def on_notification_received(self, message):
        play_alert_sound()
        QMessageBox.information(self, "Уведомление от Директора", message)

    def on_screen_requested(self):
        self.screen_active = True
        self.start_screen_stream()

    def on_stop_screen_requested(self):
        self.screen_active = False
        if self.screen_timer:
            self.screen_timer.stop()
            self.screen_timer = None

    def start_screen_stream(self):
        if self.screen_timer is None:
            self.screen_timer = QTimer()
            self.screen_timer.timeout.connect(self.capture_and_send_screen)
            self.screen_timer.start(33)

    def capture_and_send_screen(self):
        if not self.screen_active:
            return
        try:
            monitor = self.sct.monitors[1]
            frame = self.sct.grab(monitor)
            img = np.array(frame)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img_resized = cv2.resize(img, (800, 600), interpolation=cv2.INTER_LINEAR)
            ret, jpeg = cv2.imencode('.jpg', img_resized, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if not ret:
                return
            img_str = base64.b64encode(jpeg.tobytes()).decode()
            if len(img_str) < 300000:
                self.client_thread.send_screen('Director', img_str)
        except Exception:
            pass

    def send_message(self, input_widget):
        message = input_widget.text().strip()
        if not message:
            return
        current_tab = self.chat_tabs.currentWidget()
        tab_text = self.chat_tabs.tabText(self.chat_tabs.currentIndex())
        if tab_text == "Общий чат":
            if self.client_thread.send_message('general', message):
                self.append_chat_line(self.general_chat.chat_display, f"[{datetime.now().strftime('%H:%M:%S')}] Я: {message}")
                input_widget.clear()
        else:
            if self.client_thread.send_message('Director', message):
                self.append_chat_line(self.private_chat.chat_display, f"[{datetime.now().strftime('%H:%M:%S')}] Я: {message}")
                input_widget.clear()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.showMinimized()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = app.font()
    font.setFamily("Arial")
    font.setPointSize(10)
    app.setFont(font)
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        sock, username, password, screen_stream = login_dialog.get_socket_and_credentials()
        main_window = MainWindow(sock, username, password, screen_stream)
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

main()