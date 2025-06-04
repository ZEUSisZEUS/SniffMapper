import sys
import os
from scapy.all import sniff, IP, TCP, UDP, DNS, Raw, ICMP, IPv6, ARP, conf, get_if_list
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QPushButton, 
                             QComboBox, QLineEdit, QLabel, QMessageBox, QHeaderView)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl
from PyQt5.QtGui import QFont, QFontDatabase, QColor, QPalette, QIcon
import queue
from datetime import datetime
import requests
import logging
import time
from requests.exceptions import HTTPError
import ipaddress
import math
import json
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cyberpunk color palette
CYBER_BLUE = "#00f0ff"
CYBER_PURPLE = "#bd00ff"
CYBER_GREEN = "#00ff9d"
CYBER_RED = "#ff003c"
CYBER_ORANGE = "#ff6200"
CYBER_YELLOW = "#ffe600"
CYBER_DARK = "#0a0a0a"
CYBER_DARKER = "#050505"
CYBER_LIGHT = "#e0e0e0"

# HTML content for the cyberpunk map
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberTech Network Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #050505;
            color: #00f0ff;
            font-family: 'Courier New', monospace;
            height: 100vh;
            overflow: hidden;
        }
        #map {
            height: 100%;
            width: 100%;
            background: #050505;
        }
        .cyber-marker {
            position: relative;
            width: 40px;
            height: 40px;
        }
        .marker-core {
            position: absolute;
            width: 12px;
            height: 12px;
            background: #00f0ff;
            border: 2px solid #050505;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 15px #00f0ff;
            z-index: 4;
        }
        .marker-pulse {
            position: absolute;
            width: 30px;
            height: 30px;
            background: #00f0ff;
            border-radius: 50%;
            opacity: 0.3;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            animation: pulse 2s infinite ease-out;
            z-index: 1;
        }
        .marker-ring {
            position: absolute;
            border: 2px solid #00f0ff;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 10px #00f0ff;
            z-index: 3;
        }
        .marker-ring-1 {
            width: 20px;
            height: 20px;
            animation: spin 4s linear infinite;
            border-top-color: transparent;
        }
        .marker-ring-2 {
            width: 30px;
            height: 30px;
            animation: spin-reverse 5s linear infinite;
            border-right-color: transparent;
        }
        @keyframes pulse {
            0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.3; }
            50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.1; }
            100% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.3; }
        }
        @keyframes spin {
            0% { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(360deg); }
        }
        @keyframes spin-reverse {
            0% { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(-360deg); }
        }
        .cyber-tooltip {
            background-color: rgba(5, 5, 5, 0.9) !important;
            border: 1px solid #00f0ff !important;
            color: #00f0ff !important;
            font-family: 'Courier New', monospace !important;
            font-size: 12px !important;
            padding: 5px !important;
            border-radius: 3px !important;
            box-shadow: 0 0 10px #00f0ff !important;
        }
        .cyber-path {
            stroke: #00f0ff;
            stroke-width: 3;
            stroke-dasharray: 10, 10;
            stroke-linecap: round;
            animation: dash 1s linear infinite;
            filter: drop-shadow(0 0 5px #00f0ff);
        }
        @keyframes dash {
            to {
                stroke-dashoffset: 20;
            }
        }
        .scanline {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(to right, transparent, #00f0ff, transparent);
            animation: scan 3s linear infinite;
            z-index: 1000;
            pointer-events: none;
            opacity: 0.7;
        }
        @keyframes scan {
            0% { transform: translateY(0); }
            100% { transform: translateY(100vh); }
        }
        .grid-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                linear-gradient(rgba(0, 240, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 240, 255, 0.05) 1px, transparent 1px);
            background-size: 20px 20px;
            pointer-events: none;
            z-index: 500;
        }
        #info-panel {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(5, 5, 5, 0.9);
            border: 1px solid #00f0ff;
            color: #00f0ff;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            z-index: 1000;
            box-shadow: 0 0 10px #00f0ff;
            max-width: 300px;
        }
        #control-panel {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(5, 5, 5, 0.9);
            border: 1px solid #00f0ff;
            color: #00f0ff;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            z-index: 1000;
            box-shadow: 0 0 10px #00f0ff;
        }
        .control-btn {
            background: rgba(0, 240, 255, 0.1);
            border: 1px solid #00f0ff;
            color: #00f0ff;
            padding: 5px;
            margin: 3px 0;
            border-radius: 3px;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            transition: all 0.3s;
        }
        .control-btn:hover {
            background: rgba(0, 240, 255, 0.3);
            box-shadow: 0 0 5px #00f0ff;
        }
        .leaflet-container {
            background: #050505 !important;
        }
        .leaflet-tile {
            filter: brightness(0.6) contrast(1.2) grayscale(50%) sepia(100%) hue-rotate(160deg) saturate(3);
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="scanline"></div>
    <div class="grid-overlay"></div>
    
    <div id="info-panel">
        <div id="distance-info">Select packets to trace network paths</div>
        <div id="packet-info" style="margin-top: 10px;"></div>
    </div>
    
    <div id="control-panel">
        <div style="margin-bottom: 10px;">CYBERTECH NETWORK MAP</div>
        <div style="display: flex; flex-direction: column;">
            <input id="search-input" type="text" placeholder="Search location..." class="control-btn" style="margin-bottom: 5px;">
            <button id="search-btn" class="control-btn">SEARCH</button>
            <button id="unit-toggle" class="control-btn">TOGGLE KM/MILES</button>
            <button id="reset-btn" class="control-btn">RESET MAP</button>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Initialize cyberpunk map
        const map = L.map('map').setView([0, 0], 2);
        
        // Dark cyberpunk tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        
        // Store markers and paths
        let markers = [];
        let paths = [];
        let isKm = true;
        
        // Create cyberpunk marker
        function createCyberMarker() {
            const markerDiv = document.createElement('div');
            markerDiv.className = 'cyber-marker';
            markerDiv.innerHTML = `
                <div class="marker-pulse"></div>
                <div class="marker-ring marker-ring-1"></div>
                <div class="marker-ring marker-ring-2"></div>
                <div class="marker-core"></div>
            `;
            return markerDiv;
        }
        
        // Add marker to map
        function addMarker(lat, lng, popup) {
            const marker = L.marker([lat, lng], {
                icon: L.divIcon({
                    className: 'cyber-marker-icon',
                    html: createCyberMarker().outerHTML,
                    iconSize: [40, 40],
                    iconAnchor: [20, 40]
                })
            }).bindTooltip(popup, {
                permanent: false,
                direction: 'top',
                className: 'cyber-tooltip'
            }).addTo(map);
            
            markers.push(marker);
            return marker;
        }
        
        // Add path between points
        function addPath(point1, point2) {
            const path = L.polyline([point1, point2], {
                color: '#00f0ff',
                weight: 3,
                dashArray: '10, 10',
                className: 'cyber-path'
            }).addTo(map);
            
            paths.push(path);
            return path;
        }
        
        // Calculate distance between points
        function calculateDistance(lat1, lon1, lat2, lon2) {
            const R = isKm ? 6371 : 3958.8; // Earth radius in km or miles
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = 
                Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
                Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return (R * c).toFixed(2);
        }
        
        // Clear all markers and paths
        function clearMap() {
            markers.forEach(marker => map.removeLayer(marker));
            paths.forEach(path => map.removeLayer(path));
            markers = [];
            paths = [];
            document.getElementById('distance-info').innerText = 'Select packets to trace network paths';
            document.getElementById('packet-info').innerHTML = '';
        }
        
        // Add network path from packet data
        function addNetworkPath(packetData) {
            clearMap();
            
            const validLocations = [];
            packetData.forEach(packet => {
                if (packet.lat && packet.lng && packet.lat !== 'N/A' && packet.lng !== 'N/A') {
                    validLocations.push({
                        lat: parseFloat(packet.lat),
                        lng: parseFloat(packet.lng),
                        popup: packet.popup,
                        info: packet.info
                    });
                }
            });
            
            if (validLocations.length === 0) {
                document.getElementById('distance-info').innerText = 'No valid locations found';
                return;
            }
            
            // Add markers for all locations
            validLocations.forEach(loc => {
                addMarker(loc.lat, loc.lng, loc.popup);
            });
            
            // Connect markers with paths if we have exactly 2 points
            if (validLocations.length === 2) {
                const point1 = [validLocations[0].lat, validLocations[0].lng];
                const point2 = [validLocations[1].lat, validLocations[1].lng];
                addPath(point1, point2);
                
                const distance = calculateDistance(
                    validLocations[0].lat, validLocations[0].lng,
                    validLocations[1].lat, validLocations[1].lng
                );
                
                document.getElementById('distance-info').innerText = 
                    `DISTANCE: ${distance} ${isKm ? 'KM' : 'MILES'}`;
                    
                document.getElementById('packet-info').innerHTML = 
                    `<div style="border-bottom: 1px solid #00f0ff; padding-bottom: 5px; margin-bottom: 5px;">PACKET INFO</div>
                     <div>${validLocations[0].info.replace(/\\n/g, '<br>')}</div>
                     <div style="margin-top: 10px;">${validLocations[1].info.replace(/\\n/g, '<br>')}</div>`;
                
                // Fit bounds to show both markers
                map.fitBounds([point1, point2], { padding: [50, 50] });
            } else if (validLocations.length === 1) {
                map.setView([validLocations[0].lat, validLocations[0].lng], 13);
                document.getElementById('packet-info').innerHTML = 
                    `<div style="border-bottom: 1px solid #00f0ff; padding-bottom: 5px; margin-bottom: 5px;">PACKET INFO</div>
                     <div>${validLocations[0].info.replace(/\\n/g, '<br>')}</div>`;
            }
        }
        
        // Control panel event handlers
        document.getElementById('search-btn').addEventListener('click', () => {
            const query = document.getElementById('search-input').value;
            if (query) {
                fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.length > 0) {
                            const { lat, lon } = data[0];
                            map.setView([lat, lon], 13);
                        } else {
                            console.log('Location not found');
                        }
                    })
                    .catch(error => console.error('Search error:', error));
            }
        });
        
        document.getElementById('unit-toggle').addEventListener('click', () => {
            isKm = !isKm;
            document.getElementById('unit-toggle').innerText = isKm ? 'TOGGLE MILES' : 'TOGGLE KM';
            
            // Update distance display if we have exactly 2 markers
            if (markers.length === 2) {
                const point1 = markers[0].getLatLng();
                const point2 = markers[1].getLatLng();
                const distance = calculateDistance(
                    point1.lat, point1.lng,
                    point2.lat, point2.lng
                );
                document.getElementById('distance-info').innerText = 
                    `DISTANCE: ${distance} ${isKm ? 'KM' : 'MILES'}`;
            }
        });
        
        document.getElementById('reset-btn').addEventListener('click', clearMap);
        
        // Make the function available globally
        window.addNetworkPath = addNetworkPath;
    </script>
</body>
</html>
"""

class SnifferThread(QThread):
    packet_received = pyqtSignal(object)

    def __init__(self, filter_text, interface):
        super().__init__()
        self.filter_text = filter_text
        self.interface = interface
        self.stopped = False

    def run(self):
        try:
            sniff(filter=self.filter_text, iface=self.interface, prn=self.packet_handler, 
                  store=False, stop_filter=lambda x: self.stopped)
        except Exception as e:
            logging.error(f"Sniffing error: {e}")
            QMessageBox.critical(None, "ERROR", f"Sniffing failed: {e}")

    def packet_handler(self, packet):
        if not self.stopped:
            self.packet_received.emit(packet)

    def stop(self):
        self.stopped = True

class CyberTechPacketTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CYBERTECH PACKET TRACKER")
        self.setGeometry(100, 100, 1280, 800)
        
        # Load cyberpunk font
        self.load_fonts()
        
        # Set cyberpunk palette
        self.set_cyberpunk_style()
        
        # Flag to prevent multiple simultaneous scans
        self.geo_scan_in_progress = False
        
        # Set up main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header with cyberpunk styling
        self.header = QLabel("CYBERTECH PACKET TRACKER")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet(f"""
            background-color: {CYBER_DARK};
            color: {CYBER_BLUE};
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
            border-bottom: 2px solid {CYBER_BLUE};
            text-shadow: 0 0 10px {CYBER_BLUE};
        """)
        main_layout.addWidget(self.header)
        
        # Create tabs with cyberpunk styling
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {CYBER_BLUE};
                background: {CYBER_DARK};
            }}
            QTabBar::tab {{
                background: {CYBER_DARK};
                color: {CYBER_BLUE};
                border: 1px solid {CYBER_BLUE};
                padding: 8px;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background: {CYBER_BLUE};
                color: {CYBER_DARK};
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background: rgba(0, 240, 255, 0.3);
            }}
        """)
        main_layout.addWidget(self.tabs)
        
        # Packet List Tab
        self.packet_list_widget = QWidget()
        packet_list_layout = QVBoxLayout()
        self.packet_list_widget.setLayout(packet_list_layout)
        
        # Packet table with cyber styling
        self.packet_table = QTableWidget()
        self.packet_table.setColumnCount(6)
        self.packet_table.setHorizontalHeaderLabels(['TIME', 'SOURCE', 'DEST', 'PROTO', 'SIZE', 'INFO'])
        self.packet_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                border: 1px solid {CYBER_BLUE};
                font-family: 'Courier New';
                font-size: 11px;
                gridline-color: rgba(0, 240, 255, 0.2);
            }}
            QHeaderView::section {{
                background-color: {CYBER_DARKER};
                color: {CYBER_BLUE};
                padding: 5px;
                border: 1px solid {CYBER_BLUE};
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 3px;
            }}
            QTableWidget::item:selected {{
                background-color: {CYBER_BLUE};
                color: {CYBER_DARK};
            }}
        """)
        
        # Set column widths
        self.packet_table.setColumnWidth(0, 120)  # Time
        self.packet_table.setColumnWidth(1, 180)  # Source
        self.packet_table.setColumnWidth(2, 180)  # Dest
        self.packet_table.setColumnWidth(3, 70)   # Protocol
        self.packet_table.setColumnWidth(4, 60)   # Length
        self.packet_table.setColumnWidth(5, 400)  # Info
        
        # Enable sorting
        self.packet_table.setSortingEnabled(True)
        self.packet_table.sortByColumn(0, Qt.AscendingOrder)
        
        # Selection behavior
        self.packet_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.packet_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.packet_table.selectionModel().selectionChanged.connect(self.show_packet_details)
        
        packet_list_layout.addWidget(self.packet_table)
        self.tabs.addTab(self.packet_list_widget, "PACKET LIST")
        
        # Packet Details Tab
        self.packet_details_widget = QWidget()
        packet_details_layout = QVBoxLayout()
        self.packet_details_widget.setLayout(packet_details_layout)
        
        self.details_text = QTextEdit()
        self.details_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                border: 1px solid {CYBER_BLUE};
                font-family: 'Courier New';
                font-size: 11px;
                selection-background-color: {CYBER_BLUE};
                selection-color: {CYBER_DARK};
            }}
        """)
        self.details_text.setReadOnly(True)
        packet_details_layout.addWidget(self.details_text)
        self.tabs.addTab(self.packet_details_widget, "PACKET INSPECTOR")
        
        # Hex Dump Tab
        self.hex_widget = QWidget()
        hex_layout = QVBoxLayout()
        self.hex_widget.setLayout(hex_layout)
        
        self.hex_text = QTextEdit()
        self.hex_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                border: 1px solid {CYBER_BLUE};
                font-family: 'Courier New';
                font-size: 11px;
                selection-background-color: {CYBER_BLUE};
                selection-color: {CYBER_DARK};
            }}
        """)
        self.hex_text.setReadOnly(True)
        hex_layout.addWidget(self.hex_text)
        self.tabs.addTab(self.hex_widget, "HEX ANALYZER")
        
        # Network Map Tab
        self.map_widget = QWidget()
        map_layout = QVBoxLayout()
        self.map_widget.setLayout(map_layout)
        map_layout.setContentsMargins(0, 0, 0, 0)
        
        self.map_view = QWebEngineView()
        self.map_view.setHtml(HTML_CONTENT)
        map_layout.addWidget(self.map_view)
        self.tabs.addTab(self.map_widget, "NETWORK MAP")
        
        # Control Panel
        control_widget = QWidget()
        control_layout = QHBoxLayout()
        control_widget.setLayout(control_layout)
        control_widget.setStyleSheet(f"background-color: {CYBER_DARKER};")
        control_layout.setContentsMargins(10, 5, 10, 5)
        
        # Interface selection
        interface_label = QLabel("INTERFACE:")
        interface_label.setStyleSheet(f"color: {CYBER_BLUE}; font-family: 'Courier New'; font-size: 11px;")
        control_layout.addWidget(interface_label)
        
        self.interface_combo = QComboBox()
        self.interface_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                border: 1px solid {CYBER_BLUE};
                font-family: 'Courier New';
                font-size: 11px;
                padding: 3px;
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                selection-background-color: {CYBER_BLUE};
                selection-color: {CYBER_DARK};
            }}
        """)
        
        interfaces = get_if_list()
        if interfaces:
            self.interface_combo.addItems(interfaces)
        control_layout.addWidget(self.interface_combo)
        
        # Filter
        filter_label = QLabel("FILTER:")
        filter_label.setStyleSheet(f"color: {CYBER_BLUE}; font-family: 'Courier New'; font-size: 11px;")
        control_layout.addWidget(filter_label)
        
        self.filter_entry = QLineEdit()
        self.filter_entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                border: 1px solid {CYBER_BLUE};
                font-family: 'Courier New';
                font-size: 11px;
                padding: 3px;
                min-width: 200px;
            }}
        """)
        self.filter_entry.setText("ip or ip6")
        control_layout.addWidget(self.filter_entry)
        
        # Buttons
        self.create_cyber_button("START", self.start_sniffing, control_layout)
        self.create_cyber_button("STOP", self.stop_sniffing, control_layout, False)
        self.create_cyber_button("GEO SCAN", self.scan_selected_packet_geo, control_layout)
        self.create_cyber_button("MAP TRACE", self.show_in_map, control_layout)
        self.create_cyber_button("CLEAR", self.clear_display, control_layout)
        
        # Status
        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setStyleSheet(f"""
            color: {CYBER_BLUE};
            font-family: 'Courier New';
            font-size: 11px;
            font-weight: bold;
            padding: 5px;
            border: 1px solid {CYBER_BLUE};
            min-width: 150px;
            text-align: center;
        """)
        control_layout.addWidget(self.status_label)
        
        # Add some stretch
        control_layout.addStretch()
        
        main_layout.addWidget(control_widget)
        
        # Sniffer control
        self.sniffer_thread = None
        self.packet_queue = queue.Queue()
        self.packets = []
        
        # Start processing packets
        self.process_packet_queue()
    
    def load_fonts(self):
        # Try to load a cyberpunk-style font
        font_db = QFontDatabase()
        if "Courier New" in font_db.families():
            cyber_font = QFont("Courier New", 10)
            cyber_font.setBold(True)
            QApplication.setFont(cyber_font)
        else:
            # Fallback to monospace
            fallback_font = QFont("Monospace", 10)
            fallback_font.setBold(True)
            QApplication.setFont(fallback_font)
    
    def set_cyberpunk_style(self):
        # Set the overall application style
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(CYBER_DARKER))
        palette.setColor(QPalette.WindowText, QColor(CYBER_BLUE))
        palette.setColor(QPalette.Base, QColor(CYBER_DARK))
        palette.setColor(QPalette.AlternateBase, QColor(CYBER_DARKER))
        palette.setColor(QPalette.ToolTipBase, QColor(CYBER_DARK))
        palette.setColor(QPalette.ToolTipText, QColor(CYBER_BLUE))
        palette.setColor(QPalette.Text, QColor(CYBER_BLUE))
        palette.setColor(QPalette.Button, QColor(CYBER_DARK))
        palette.setColor(QPalette.ButtonText, QColor(CYBER_BLUE))
        palette.setColor(QPalette.BrightText, QColor(CYBER_RED))
        palette.setColor(QPalette.Highlight, QColor(CYBER_BLUE))
        palette.setColor(QPalette.HighlightedText, QColor(CYBER_DARK))
        QApplication.setPalette(palette)
        
        # Additional style tweaks
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {CYBER_DARKER};
                border: 2px solid {CYBER_BLUE};
            }}
            QStatusBar {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                font-family: 'Courier New';
            }}
            QMenuBar {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
            }}
            QMenuBar::item {{
                background-color: transparent;
            }}
            QMenuBar::item:selected {{
                background-color: {CYBER_BLUE};
                color: {CYBER_DARK};
            }}
            QMenu {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                border: 1px solid {CYBER_BLUE};
            }}
            QMenu::item:selected {{
                background-color: {CYBER_BLUE};
                color: {CYBER_DARK};
            }}
        """)
    
    def create_cyber_button(self, text, callback, layout, enabled=True):
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {CYBER_DARK};
                color: {CYBER_BLUE};
                border: 1px solid {CYBER_BLUE};
                font-family: 'Courier New';
                font-size: 11px;
                font-weight: bold;
                padding: 5px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 240, 255, 0.3);
                border: 1px solid {CYBER_PURPLE};
            }}
            QPushButton:pressed {{
                background-color: {CYBER_BLUE};
                color: {CYBER_DARK};
            }}
            QPushButton:disabled {{
                background-color: {CYBER_DARKER};
                color: rgba(0, 240, 255, 0.5);
                border: 1px solid rgba(0, 240, 255, 0.3);
            }}
        """)
        button.clicked.connect(callback)
        button.setEnabled(enabled)
        layout.addWidget(button)
        
        # Store reference to important buttons
        if text == "START":
            self.start_button = button
        elif text == "STOP":
            self.stop_button = button
        elif text == "GEO SCAN":
            self.geo_button = button
    
    def process_packet_queue(self):
        try:
            while True:
                packet = self.packet_queue.get_nowait()
                self.packets.append(packet)
                self.add_packet_to_table(packet)
        except queue.Empty:
            pass
        QApplication.processEvents()
        QTimer.singleShot(100, self.process_packet_queue)
    
    def add_packet_to_table(self, packet):
        time_str = datetime.fromtimestamp(packet.time).strftime('%H:%M:%S.%f')[:-3]
        src = dst = "UNKNOWN"
        
        if IP in packet:
            src = packet[IP].src
            dst = packet[IP].dst
        elif IPv6 in packet:
            src = packet[IPv6].src
            dst = packet[IPv6].dst
        elif ARP in packet:
            src = packet[ARP].psrc
            dst = packet[ARP].pdst
        
        protocol = self.get_protocol_name(packet)
        length = len(packet)
        info = self.get_packet_info(packet)
        
        row = self.packet_table.rowCount()
        self.packet_table.insertRow(row)
        
        # Create items with cyberpunk styling
        time_item = QTableWidgetItem(time_str)
        src_item = QTableWidgetItem(src)
        dst_item = QTableWidgetItem(dst)
        proto_item = QTableWidgetItem(protocol)
        length_item = QTableWidgetItem(str(length))
        info_item = QTableWidgetItem(info)
        
        # Set items in table
        self.packet_table.setItem(row, 0, time_item)
        self.packet_table.setItem(row, 1, src_item)
        self.packet_table.setItem(row, 2, dst_item)
        self.packet_table.setItem(row, 3, proto_item)
        self.packet_table.setItem(row, 4, length_item)
        self.packet_table.setItem(row, 5, info_item)
        
        # Color code packets by protocol
        color = CYBER_BLUE  # Default
        if protocol == "TCP":
            color = CYBER_GREEN
        elif protocol == "UDP":
            color = CYBER_PURPLE
        elif protocol == "HTTP":
            color = CYBER_YELLOW
        elif protocol == "HTTPS":
            color = CYBER_ORANGE
        elif protocol == "DNS":
            color = CYBER_RED
        
        for col in range(6):
            self.packet_table.item(row, col).setForeground(QColor(color))
        
        self.packet_table.scrollToBottom()
    
    def get_protocol_name(self, packet):
        if TCP in packet:
            if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                return "HTTP"
            if packet[TCP].dport == 443 or packet[TCP].sport == 443:
                return "HTTPS"
            if packet[TCP].dport == 53 or packet[TCP].sport == 53:
                return "DNS"
            return "TCP"
        elif UDP in packet:
            if packet[UDP].dport == 53 or packet[UDP].sport == 53:
                return "DNS"
            return "UDP"
        elif ICMP in packet:
            return "ICMP"
        elif ARP in packet:
            return "ARP"
        elif IPv6 in packet:
            return "IPv6"
        return "OTHER"
    
    def get_packet_info(self, packet):
        info = ""
        if TCP in packet:
            tcp = packet[TCP]
            info = f"TCP {tcp.sport} → {tcp.dport} [Flags: {self.get_tcp_flags(tcp)}]"
            if tcp.dport == 80 or tcp.sport == 80:
                if Raw in packet:
                    try:
                        load = packet[Raw].load.decode('ascii', errors='ignore')
                        if 'HTTP' in load:
                            first_line = load.split('\r\n')[0]
                            info = f"HTTP: {first_line}"
                    except:
                        pass
        elif UDP in packet:
            udp = packet[UDP]
            info = f"UDP {udp.sport} → {udp.dport}"
            if (udp.dport == 53 or udp.sport == 53) and DNS in packet:
                dns = packet[DNS]
                if dns.qr == 0:
                    if dns.qd:
                        info = f"DNS Query: {dns.qd.qname.decode('utf-8')}"
                else:
                    if dns.an:
                        info = f"DNS Response: {dns.an[0].rdata if dns.an else 'N/A'}"
        elif ICMP in packet:
            icmp = packet[ICMP]
            info = f"ICMP Type: {icmp.type}, Code: {icmp.code}"
        elif ARP in packet:
            arp = packet[ARP]
            if arp.op == 1:
                info = f"ARP Who has {arp.pdst}? Tell {arp.psrc}"
            elif arp.op == 2:
                info = f"ARP {arp.psrc} is at {arp.hwsrc}"
        return info
    
    def get_tcp_flags(self, tcp):
        flags = []
        if tcp.flags & 0x01:
            flags.append("FIN")
        if tcp.flags & 0x02:
            flags.append("SYN")
        if tcp.flags & 0x04:
            flags.append("RST")
        if tcp.flags & 0x08:
            flags.append("PSH")
        if tcp.flags & 0x10:
            flags.append("ACK")
        if tcp.flags & 0x20:
            flags.append("URG")
        return '/'.join(flags) if flags else "NONE"
    
    def show_packet_details(self):
        selected_rows = self.packet_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        index = selected_rows[0].row()
        if index < len(self.packets):
            packet = self.packets[index]
            
            self.details_text.setText(self.get_packet_details(packet))
            hexdump = self.hex_dump(bytes(packet))
            self.hex_text.setText(hexdump)
    
    def get_packet_details(self, packet):
        details = [
            "=== PACKET INSPECTION ===",
            f"TIMESTAMP: {datetime.fromtimestamp(packet.time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",
            f"LENGTH: {len(packet)} bytes",
            f"SUMMARY: {self.get_packet_info(packet)}"
        ]
        
        if packet.haslayer('Ether'):
            eth = packet['Ether']
            details.append("\n=== ETHERNET FRAME ===")
            details.append(f"SOURCE MAC: {eth.src}")
            details.append(f"DESTINATION MAC: {eth.dst}")
            details.append(f"TYPE: 0x{eth.type:04x}")
        
        if IP in packet:
            ip = packet[IP]
            details.append("\n=== IP DATAGRAM ===")
            details.append(f"VERSION: {ip.version}")
            details.append(f"HEADER LENGTH: {ip.ihl * 4} bytes")
            details.append(f"TOS: 0x{ip.tos:02x}")
            details.append(f"TOTAL LENGTH: {len(ip)} bytes")
            details.append(f"ID: {ip.id}")
            details.append(f"FLAGS: {ip.flags}")
            details.append(f"FRAGMENT OFFSET: {ip.frag}")
            details.append(f"TTL: {ip.ttl}")
            details.append(f"PROTOCOL: {ip.proto} ({self.get_proto_name(ip.proto)})")
            details.append(f"CHECKSUM: 0x{ip.chksum:04x}")
            details.append(f"SOURCE IP: {ip.src}")
            details.append(f"DESTINATION IP: {ip.dst}")
        elif IPv6 in packet:
            ipv6 = packet[IPv6]
            details.append("\n=== IPv6 DATAGRAM ===")
            details.append(f"VERSION: {ipv6.version}")
            details.append(f"TRAFFIC CLASS: 0x{ipv6.tc:02x}")
            details.append(f"FLOW LABEL: 0x{ipv6.fl:05x}")
            details.append(f"PAYLOAD LENGTH: {ipv6.plen}")
            details.append(f"NEXT HEADER: {ipv6.nh}")
            details.append(f"HOP LIMIT: {ipv6.hlim}")
            details.append(f"SOURCE IP: {ipv6.src}")
            details.append(f"DESTINATION IP: {ipv6.dst}")
        
        if TCP in packet:
            tcp = packet[TCP]
            details.append("\n=== TCP SEGMENT ===")
            details.append(f"SOURCE PORT: {tcp.sport}")
            details.append(f"DESTINATION PORT: {tcp.dport}")
            details.append(f"SEQUENCE NUMBER: {tcp.seq}")
            details.append(f"ACK NUMBER: {tcp.ack}")
            details.append(f"DATA OFFSET: {tcp.dataofs * 4} bytes")
            details.append(f"FLAGS: {self.get_tcp_flags(tcp)}")
            details.append(f"WINDOW SIZE: {tcp.window}")
            details.append(f"CHECKSUM: 0x{tcp.chksum:04x}")
            details.append(f"URGENT POINTER: {tcp.urgptr}")
            
            if (tcp.dport == 80 or tcp.sport == 80) and Raw in packet:
                try:
                    load = packet[Raw].load.decode('ascii')
                    if 'HTTP' in load:
                        details.append("\n=== HTTP CONTENT ===")
                        details.append(load[:500])
                except UnicodeDecodeError:
                    pass
        elif UDP in packet:
            udp = packet[UDP]
            details.append("\n=== UDP DATAGRAM ===")
            details.append(f"SOURCE PORT: {udp.sport}")
            details.append(f"DESTINATION PORT: {udp.dport}")
            details.append(f"LENGTH: {udp.len}")
            details.append(f"CHECKSUM: 0x{udp.chksum:04x}")
            
            if (udp.dport == 53 or udp.sport == 53) and DNS in packet:
                dns = packet[DNS]
                details.append("\n=== DNS MESSAGE ===")
                details.append(f"TRANSACTION ID: 0x{dns.id:04x}")
                details.append(f"FLAGS: 0x{dns.flags:04x}")
                details.append(f"QUESTIONS: {len(dns.qd) if dns.qd else 0}")
                details.append(f"ANSWER RRs: {len(dns.an) if hasattr(dns, 'an') else 0}")
                details.append(f"AUTHORITY RRs: {len(dns.ns) if dns.ns else 0}")
                details.append(f"ADDITIONAL RRs: {len(dns.ar) if hasattr(dns, 'ar') else 0}")
                
                if dns.qr == 0:
                    if dns.qd:
                        details.append(f"\nQUESTION:")
                        if hasattr(dns.qd, 'qname'):
                            details.append(f"  NAME: {dns.qd.qname.decode('ascii')}")
                        details.append(f"  TYPE: {dns.qd.qtype}")
                        details.append(f"  CLASS: {dns.qd.qclass}")
                else:
                    for i in range(len(dns.an)):
                        rr = dns.an[i]
                        details.append(f"\nANSWER {i+1}:")
                        details.append(f"  NAME: {rr.rrname.decode('ascii') if hasattr(rr, 'rrname') else ''}")
                        details.append(f"  TYPE: {rr.type if hasattr(rr, 'type') else ''}")
                        details.append(f"  CLASS: {rr.rclass if hasattr(rr, 'rclass') else ''}")
                        details.append(f"  TTL: {rr.ttl if hasattr(rr, 'ttl') else ''}")
                        details.append(f"  DATA: {rr.rdata if hasattr(rr, 'rdata') else ''}")
        
        elif ICMP in packet:
            icmp = packet[ICMP]
            details.append("\n=== ICMP MESSAGE ===")
            details.append(f"TYPE: {icmp.type}")
            details.append(f"CODE: {icmp.code}")
            details.append(f"CHECKSUM: 0x{icmp.chksum:04x}")
        
        elif ARP in packet:
            arp = packet[ARP]
            details.append("\n=== ARP MESSAGE ===")
            details.append(f"HARDWARE TYPE: {arp.hwtype}")
            details.append(f"PROTOCOL TYPE: 0x{arp.ptype:04x}")
            details.append(f"HARDWARE SIZE: {arp.hwlen}")
            details.append(f"PROTOCOL SIZE: {arp.plen}")
            details.append(f"OPERATION: {self.get_arp_operation(arp.op)}")
            details.append(f"SENDER MAC: {arp.hwsrc}")
            details.append(f"SENDER IP: {arp.psrc}")
            details.append(f"TARGET MAC: {arp.hwdst}")
            details.append(f"TARGET IP: {arp.pdst}")
        
        return '\n'.join(details)
    
    def get_proto_name(self, proto_num):
        proto_names = {
            1: "ICMP",
            6: "TCP",
            17: "UDP",
            2: "IGMP",
            58: "ICMPv6",
            89: "OSPF"
        }
        return proto_names.get(proto_num, str(proto_num))
    
    def get_arp_operation(self, op):
        ops = {
            1: "ARP REQUEST",
            2: "ARP REPLY",
            3: "RARP REQUEST",
            4: "RARP REPLY"
        }
        return ops.get(op, str(op))
    
    def hex_dump(self, data):
        hex_dump = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_str = ' '.join(f"{b:02x}" for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            hex_dump.append(f"{i:08x}:  {hex_str.ljust(47)}  {ascii_str}")
        return '\n'.join(hex_dump)
    
    def start_sniffing(self):
        filter_text = self.filter_entry.text()
        if not filter_text:
            QMessageBox.critical(self, "ERROR", "PLEASE ENTER A VALID FILTER EXPRESSION")
            return
        
        # Check if running as root
        if os.geteuid() != 0:
            QMessageBox.critical(self, "PERMISSION ERROR", 
                                 "PACKET SNIFFING REQUIRES ROOT PRIVILEGES.\nPLEASE RUN WITH SUDO OR GRANT CAP_NET_RAW CAPABILITY.")
            return
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("SNIFFING...")
        self.status_label.setStyleSheet(f"""
            color: {CYBER_GREEN};
            font-family: 'Courier New';
            font-size: 11px;
            font-weight: bold;
            padding: 5px;
            border: 1px solid {CYBER_GREEN};
            min-width: 150px;
            text-align: center;
        """)
        
        interface = self.interface_combo.currentText()
        self.sniffer_thread = SnifferThread(filter_text, interface)
        self.sniffer_thread.packet_received.connect(self.packet_queue.put)
        self.sniffer_thread.start()
    
    def stop_sniffing(self):
        if self.sniffer_thread:
            self.sniffer_thread.stop()
            self.sniffer_thread.wait()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("SYSTEM READY")
        self.status_label.setStyleSheet(f"""
            color: {CYBER_BLUE};
            font-family: 'Courier New';
            font-size: 11px;
            font-weight: bold;
            padding: 5px;
            border: 1px solid {CYBER_BLUE};
            min-width: 150px;
            text-align: center;
        """)
    
    def clear_display(self):
        self.packet_table.setRowCount(0)
        self.details_text.clear()
        self.hex_text.clear()
        self.packets.clear()
        self.map_view.setHtml(HTML_CONTENT)
        self.status_label.setText("SYSTEM READY")
    
    def is_private_ip(self, ip):
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return True
    
    def get_geolocation(self, ip):
        if not ip or self.is_private_ip(ip):
            logging.info(f"Skipping geolocation for IP {ip}: Private or invalid IP")
            return {'ip': ip, 'error': 'Private or invalid IP'}
        
        logging.info(f"Requesting geolocation for {ip}")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
                response.raise_for_status()
                data = response.json()
                
                loc = data.get('loc', '')
                latitude = longitude = 'N/A'
                if loc:
                    latitude, longitude = loc.split(',')
                
                geo_data = {
                    'ip': data.get('ip', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'latitude': latitude,
                    'longitude': longitude,
                    'org': data.get('org', 'Unknown'),
                    'postal': data.get('postal', ''),
                    'timezone': data.get('timezone', '')
                }
                logging.info(f"Successfully fetched geolocation for {ip}")
                return geo_data
            except HTTPError as e:
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 5
                        logging.warning(f"Rate limit hit for {ip}, retry after {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error(f"Max retries for {ip}: Too Many Requests")
                        QMessageBox.critical(self, "API ERROR", f"GEOLOCATION FAILED FOR {ip}: RATE LIMIT EXCEEDED")
                        return {'ip': ip, 'error': 'Too Many Requests'}
                else:
                    logging.error(f"HTTP error for {ip}: {e}")
                    QMessageBox.critical(self, "API ERROR", f"GEOLOCATION FAILED FOR {ip}: {e}")
                    return {'ip': ip, 'error': str(e)}
            except requests.RequestException as e:
                logging.error(f"Error fetching geolocation for {ip}: {e}")
                QMessageBox.critical(self, "API ERROR", f"GEOLOCATION FAILED FOR {ip}: {e}")
                return {'ip': ip, 'error': str(e)}
    
    def format_geo_string(self, geo_data):
        if not geo_data or 'error' in geo_data:
            return f"ERROR: {geo_data.get('error', 'UNKNOWN')}"
        return (
            f"IP: {geo_data['ip']}\n"
            f"CITY: {geo_data['city']}\n"
            f"REGION: {geo_data['region']}\n"
            f"COUNTRY: {geo_data['country']}\n"
            f"LAT/LONG: {geo_data['latitude']}, {geo_data['longitude']}\n"
            f"ORG: {geo_data['org']}\n"
            f"POSTAL: {geo_data['postal']}\n"
            f"TIMEZONE: {geo_data['timezone']}"
        )
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371
        return c * r
    
    def generate_map_markers(self, src_geo, dst_geo, src_ip, dst_ip, protocol):
        valid_locations = []
        
        if 'latitude' in src_geo and src_geo['latitude'] != 'N/A' and 'error' not in src_geo:
            valid_locations.append({
                'lat': src_geo['latitude'],
                'lng': src_geo['longitude'],
                'popup': f"<b>SOURCE</b><br>IP: {src_ip}<br>City: {src_geo['city']}<br>Protocol: {protocol}",
                'info': self.format_geo_string(src_geo)
            })
        
        if 'latitude' in dst_geo and dst_geo['latitude'] != 'N/A' and 'error' not in dst_geo:
            valid_locations.append({
                'lat': dst_geo['latitude'],
                'lng': dst_geo['longitude'],
                'popup': f"<b>DESTINATION</b><br>IP: {dst_ip}<br>City: {dst_geo['city']}<br>Protocol: {protocol}",
                'info': self.format_geo_string(dst_geo)
            })
        
        if not valid_locations:
            logging.error("No valid geolocation data available for mapping")
            return None
        
        return valid_locations
    
    def show_in_map(self):
        selected_rows = self.packet_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "WARNING", "PLEASE SELECT A PACKET TO DISPLAY ON MAP")
            logging.warning("No packet selected for map display")
            return
        
        index = selected_rows[0].row()
        if index < len(self.packets):
            packet = self.packets[index]
            src = dst = "UNKNOWN"
            protocol = self.get_protocol_name(packet)
            
            if IP in packet:
                src = packet[IP].src
                dst = packet[IP].dst
            elif IPv6 in packet:
                src = packet[IPv6].src
                dst = packet[IPv6].dst
            elif ARP in packet:
                src = packet[ARP].psrc
                dst = packet[ARP].pdst
            
            logging.info(f"Fetching geolocation for src={src}, dst={dst}")
            src_geo = self.get_geolocation(src)
            dst_geo = self.get_geolocation(dst)
            
            markers = self.generate_map_markers(src_geo, dst_geo, src, dst, protocol)
            if markers:
                js_code = f"window.addNetworkPath({json.dumps(markers)});"
                self.map_view.page().runJavaScript(js_code)
                self.tabs.setCurrentWidget(self.map_widget)
                logging.info("Network path displayed on map")
            else:
                QMessageBox.warning(self, "WARNING", "NO VALID GEOLOCATION DATA AVAILABLE FOR SELECTED PACKET")
    
    def scan_selected_packet_geo(self):
        if self.geo_scan_in_progress:
            QMessageBox.warning(self, "WARNING", "GEOLOCATION SCAN ALREADY IN PROGRESS")
            logging.warning("Geolocation scan already in progress")
            return
        
        selected_rows = self.packet_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "WARNING", "PLEASE SELECT A PACKET TO SCAN")
            logging.warning("No packet selected for geolocation scan")
            return
        
        self.geo_scan_in_progress = True
        self.geo_button.setEnabled(False)
        self.status_label.setText("GEO SCAN IN PROGRESS...")
        self.status_label.setStyleSheet(f"""
            color: {CYBER_ORANGE};
            font-family: 'Courier New';
            font-size: 11px;
            font-weight: bold;
            padding: 5px;
            border: 1px solid {CYBER_ORANGE};
            min-width: 150px;
            text-align: center;
        """)
        
        try:
            index = selected_rows[0].row()
            if index < len(self.packets):
                packet = self.packets[index]
                src = dst = "UNKNOWN"
                protocol = self.get_protocol_name(packet)
                
                if IP in packet:
                    src = packet[IP].src
                    dst = packet[IP].dst
                elif IPv6 in packet:
                    src = packet[IPv6].src
                    dst = packet[IPv6].dst
                elif ARP in packet:
                    src = packet[ARP].psrc
                    dst = packet[ARP].pdst
                
                src_geo = self.get_geolocation(src)
                dst_geo = self.get_geolocation(dst)
                
                details = self.get_packet_details(packet)
                details += "\n\n=== GEOLOCATION DATA ==="
                details += f"\nSOURCE IP: {src}\nPROTOCOL: {protocol}\n"
                details += self.format_geo_string(src_geo) + "\n\n"
                details += f"DESTINATION IP: {dst}\nPROTOCOL: {protocol}\n"
                details += self.format_geo_string(dst_geo)
                self.details_text.setText(details)
                
                # Show distance if we have both locations
                if (src_geo.get('latitude') not in ['N/A', None] and 
                    dst_geo.get('latitude') not in ['N/A', None] and
                    'error' not in src_geo and 'error' not in dst_geo):
                    distance = self.calculate_distance(
                        src_geo['latitude'], src_geo['longitude'],
                        dst_geo['latitude'], dst_geo['longitude']
                    )
                    details += f"\n\nDISTANCE: {distance:.2f} km"
                    self.details_text.setText(details)
        finally:
            self.geo_scan_in_progress = False
            self.geo_button.setEnabled(True)
            self.status_label.setText("SYSTEM READY")
            self.status_label.setStyleSheet(f"""
                color: {CYBER_BLUE};
                font-family: 'Courier New';
                font-size: 11px;
                font-weight: bold;
                padding: 5px;
                border: 1px solid {CYBER_BLUE};
                min-width: 150px;
                text-align: center;
            """)

if __name__ == "__main__":
    # Check if running as root and add --no-sandbox for QWebEngineView
    if os.geteuid() == 0:
        if '--no-sandbox' not in sys.argv:
            sys.argv.append('--no-sandbox')
        logging.info("Running as root, --no-sandbox flag added for QWebEngineView")
    else:
        logging.info("Running as non-root user")
    
    app = QApplication(sys.argv)
    window = CyberTechPacketTracker()
    window.show()
    sys.exit(app.exec_())
