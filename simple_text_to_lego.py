#!/usr/bin/env python3
"""Simple Text-to-LEGO Generator - Clean and Focused"""

import os
import sys
import json
import random
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

app = Flask(__name__)
CORS(app)

# Configuration
OUTPUT_FOLDER = Path('outputs')
OUTPUT_FOLDER.mkdir(exist_ok=True)

@app.route('/')
def index():
    """Serve the simple text-to-LEGO interface."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>BrickGPT - 3D LEGO Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .viewer-area {
            height: 60vh;
            position: relative;
            background: #2c3e50;
            border-bottom: 3px solid rgba(255,255,255,0.1);
            flex-shrink: 0;
        }
        
        #three-canvas {
            width: 100%;
            height: 100%;
            display: block;
        }
        
        .viewer-controls {
            position: absolute;
            top: 15px;
            left: 15px;
            z-index: 100;
            display: flex;
            gap: 8px;
        }
        
        .viewer-btn {
            padding: 8px 12px;
            background: rgba(52, 152, 219, 0.9);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .viewer-btn:hover {
            background: rgba(52, 152, 219, 1);
            transform: translateY(-1px);
        }
        
        .viewer-info {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 12px;
            border-radius: 6px;
            font-size: 12px;
            backdrop-filter: blur(10px);
            max-width: 200px;
        }
        
        .viewer-info h3 {
            margin: 0 0 8px 0;
            font-size: 14px;
        }
        
        .model-selector {
            position: absolute;
            bottom: 15px;
            left: 15px;
            right: 15px;
            display: flex;
            gap: 8px;
            align-items: center;
            background: rgba(0,0,0,0.7);
            padding: 12px;
            border-radius: 6px;
            backdrop-filter: blur(10px);
        }
        
        .model-selector select {
            flex: 1;
            padding: 6px;
            border: none;
            border-radius: 4px;
            background: white;
            font-size: 12px;
        }
        
        .container { 
            height: 40vh;
            max-width: 90%; 
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            background: white; 
            padding: 15px 25px; 
            border-radius: 15px 15px 0 0; 
            box-shadow: 0 -10px 30px rgba(0,0,0,0.2);
            overflow-y: auto;
            flex-shrink: 0;
        }
        
        .header { 
            text-align: center; 
            margin-bottom: 15px;
        }
        
        .header h1 { 
            font-size: 1.8em; 
            margin-bottom: 3px;
            background: linear-gradient(45deg, #3498db, #9b59b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            font-size: 0.9em;
            color: #7f8c8d;
            margin: 0;
        }
        
        .form-group { 
            margin: 12px 0; 
        }
        
        label { 
            display: block; 
            font-weight: bold; 
            margin-bottom: 4px; 
            color: #2c3e50;
            font-size: 0.9em;
        }
        
        textarea { 
            width: 100%; 
            padding: 10px; 
            border: 2px solid #bdc3c7; 
            border-radius: 6px; 
            font-size: 13px;
            font-family: inherit;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
            resize: vertical;
            min-height: 60px;
            max-height: 100px;
        }
        
        textarea:focus { 
            outline: none; 
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }
        
        .input-row {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 15px;
            align-items: end;
        }
        
        input {
            width: 100%; 
            padding: 10px; 
            border: 2px solid #bdc3c7; 
            border-radius: 6px; 
            font-size: 13px;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
        }
        
        input:focus {
            outline: none; 
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }
        
        .generate-btn { 
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 15px; 
            cursor: pointer; 
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
            margin-top: 10px;
        }
        
        .generate-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }
        
        .generate-btn:disabled { 
            background: #95a5a6; 
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .result { 
            margin: 10px 0; 
            padding: 12px; 
            background: #d5f4e6; 
            border-radius: 6px; 
            border-left: 3px solid #27ae60;
            animation: slideIn 0.3s ease;
            font-size: 13px;
        }
        
        .error { 
            background: #f8d7da; 
            border-left-color: #dc3545; 
        }
        
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); 
            gap: 8px; 
            margin: 12px 0; 
        }
        
        .stat-item { 
            text-align: center; 
            padding: 8px; 
            background: white; 
            border-radius: 4px; 
            border: 1px solid #dee2e6;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .stat-value { 
            font-size: 1.2em; 
            font-weight: bold; 
            color: #3498db; 
        }
        
        .stat-label { 
            font-size: 0.7em; 
            color: #6c757d; 
            margin-top: 1px;
        }
        
        .download-links { 
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .download-links a { 
            padding: 8px 15px; 
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white; 
            text-decoration: none; 
            border-radius: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
            font-size: 14px;
        }
        
        .download-links a:hover { 
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.4);
        }
        
        .tip {
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 6px;
            padding: 10px;
            margin-top: 10px;
            color: #0c5460;
            font-size: 12px;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .loading {
            display: inline-block;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- 3D Viewer Area -->
    <div class="viewer-area">
        <canvas id="three-canvas"></canvas>
        
        <div class="viewer-controls">
            <button class="viewer-btn" onclick="clearScene()">🗑️ Clear Scene</button>
            <button class="viewer-btn" onclick="resetCamera()">🏠 Reset View</button>
            <button class="viewer-btn" onclick="toggleWireframe()">📐 Wireframe</button>
            <button class="viewer-btn" onclick="randomizeColors()">🎨 Random Colors</button>
        </div>
        
        <div class="viewer-info">
            <div id="model-info">
                <h3>🧱 LEGO 3D Viewer</h3>
                <p>Generate models below to see them here!</p>
                <div id="brick-stats" style="display: none;">
                    <strong>Current Model:</strong><br>
                    <span id="brick-count">0</span> bricks<br>
                    <span id="model-name">-</span>
                </div>
            </div>
        </div>
        
        <div class="model-selector">
            <label style="color: white; margin-right: 10px;">📂 Load Model:</label>
            <select id="modelDropdown">
                <option value="">Select a model to view...</option>
            </select>
            <button class="viewer-btn" onclick="loadSelectedModel()">Load</button>
            <button class="viewer-btn" onclick="refreshModelList()">🔄</button>
        </div>
    </div>

    <!-- Chat Interface at Bottom -->
    <div class="container">
        <div class="header">
            <h1>🧱 BrickGPT</h1>
            <p>Transform your ideas into LEGO creations</p>
        </div>
        
        <div class="form-group">
            <label>✨ Describe your LEGO creation:</label>
            <textarea id="prompt" placeholder="Example: A medieval castle with tall towers, stone walls, and colorful flags. Include a drawbridge, battlements, and make it detailed with windows and doors."></textarea>
        </div>
        
        <div class="input-row">
            <div class="form-group">
                <label>📝 Model name:</label>
                <input type="text" id="filename" value="my_lego_creation">
            </div>
            <div class="form-group">
                <label>🎲 Seed:</label>
                <input type="number" id="seed" value="42">
            </div>
            <div class="form-group">
                <label>&nbsp;</label>
                <button class="generate-btn" onclick="generateModel()">
                    🚀 Generate
                </button>
            </div>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        // Three.js 3D Scene Setup
        let scene, camera, renderer, controls;
        let currentModel = null;
        let wireframeMode = false;
        
        // LEGO Colors
        const LEGO_COLORS = {
            0: 0x05131D,   // Black
            1: 0x0055BF,   // Blue  
            2: 0x237841,   // Green
            4: 0xC91A09,   // Red
            6: 0x583927,   // Brown
            14: 0xF2CD37,  // Yellow
            15: 0xFFFFFF,  // White
            71: 0xE6E3E0,  // Light Gray
            72: 0x6C6E68   // Dark Gray
        };
        
        // Initialize 3D Scene
        function init3DScene() {
            const canvas = document.getElementById('three-canvas');
            
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x87CEEB); // Sky blue
            
            // Camera
            camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
            camera.position.set(50, 50, 50);
            
            // Renderer
            renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            
            // Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.1;
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(50, 100, 50);
            directionalLight.castShadow = true;
            directionalLight.shadow.mapSize.width = 2048;
            directionalLight.shadow.mapSize.height = 2048;
            scene.add(directionalLight);
            
            // Ground plane
            const groundGeometry = new THREE.PlaneGeometry(200, 200);
            const groundMaterial = new THREE.MeshLambertMaterial({ color: 0x90EE90 });
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);
            
            // Handle window resize
            window.addEventListener('resize', onWindowResize, false);
            
            // Start render loop
            animate();
            
            // Load initial models
            refreshModelList();
        }
        
        // Create LEGO brick geometry
        function createBrickGeometry(width, length, height = 1) {
            const group = new THREE.Group();
            
            // Main brick body
            const brickGeometry = new THREE.BoxGeometry(width * 8, height * 9.6, length * 8);
            const brick = new THREE.Mesh(brickGeometry);
            group.add(brick);
            
            // Studs on top
            const studGeometry = new THREE.CylinderGeometry(2.4, 2.4, 1.8, 16);
            for (let x = 0; x < width; x++) {
                for (let z = 0; z < length; z++) {
                    const stud = new THREE.Mesh(studGeometry);
                    stud.position.set(
                        (x - (width - 1) / 2) * 8,
                        height * 9.6 / 2 + 0.9,
                        (z - (length - 1) / 2) * 8
                    );
                    group.add(stud);
                }
            }
            
            return group;
        }
        
        // Create LEGO brick with material
        function createLegoBrick(width, length, color, position) {
            const brickGroup = createBrickGeometry(width, length);
            
            // Material
            const brickColor = LEGO_COLORS[color] || 0x95A5A6;
            const material = new THREE.MeshLambertMaterial({ 
                color: brickColor,
                transparent: false
            });
            
            // Apply material to all meshes
            brickGroup.children.forEach(mesh => {
                mesh.material = material;
                mesh.castShadow = true;
                mesh.receiveShadow = true;
            });
            
            // Position
            brickGroup.position.set(position[0], position[1], position[2]);
            
            return brickGroup;
        }
        
        // Parse model content and create 3D representation
        function loadModel(content, filename) {
            // Clear existing model first
            clearScene();
            
            currentModel = new THREE.Group();
            let bricks = [];
            
            // Parse content
            if (filename.endsWith('.txt')) {
                bricks = parseTXTContent(content);
            } else if (filename.endsWith('.ldr')) {
                bricks = parseLDRContent(content);
            }
            
            if (bricks.length === 0) {
                updateModelInfo('No bricks found', 0);
                return;
            }
            
            // Create 3D bricks
            bricks.forEach(brick => {
                const legoBrick = createLegoBrick(
                    brick.width,
                    brick.length,
                    brick.color,
                    brick.position
                );
                currentModel.add(legoBrick);
            });
            
            scene.add(currentModel);
            
            // Update info
            updateModelInfo(filename, bricks.length);
            
            // Center camera on model
            centerCameraOnModel();
        }
        
        // Parse TXT content
        function parseTXTContent(content) {
            const lines = content.split('\\n');
            const bricks = [];
            
            lines.forEach(line => {
                if (line.includes('brick at')) {
                    const typeMatch = line.match(/(\\d+)x(\\d+)/);
                    const posMatch = line.match(/\\(([^)]+)\\)/);
                    const colorMatch = line.match(/color (\\d+)/);
                    
                    if (typeMatch && posMatch && colorMatch) {
                        const width = parseInt(typeMatch[1]);
                        const length = parseInt(typeMatch[2]);
                        const coords = posMatch[1].split(',').map(n => parseFloat(n.trim()));
                        const color = parseInt(colorMatch[1]);
                        
                        bricks.push({
                            width: width,
                            length: length,
                            position: [coords[0] / 8, coords[1] / 8, coords[2] / 8],
                            color: color
                        });
                    }
                }
            });
            
            return bricks;
        }
        
        // Parse LDR content
        function parseLDRContent(content) {
            const lines = content.split('\\n');
            const bricks = [];
            
            lines.forEach(line => {
                const parts = line.trim().split(/\\s+/);
                if (parts[0] === '1' && parts.length >= 15) {
                    const color = parseInt(parts[1]);
                    const x = parseFloat(parts[2]) / 8;
                    const y = parseFloat(parts[3]) / 8;
                    const z = parseFloat(parts[4]) / 8;
                    const partName = parts[14];
                    
                    // Map LDraw parts to brick types
                    let width = 2, length = 4;
                    if (partName.includes('3003')) { width = 2; length = 2; }
                    else if (partName.includes('3004')) { width = 1; length = 2; }
                    else if (partName.includes('3005')) { width = 1; length = 1; }
                    else if (partName.includes('3010')) { width = 1; length = 4; }
                    
                    bricks.push({
                        width: width,
                        length: length,
                        position: [x, y, z],
                        color: color
                    });
                }
            });
            
            return bricks;
        }
        
        // Update model info display
        function updateModelInfo(filename, brickCount) {
            const modelInfo = document.getElementById('model-info');
            const brickStats = document.getElementById('brick-stats');
            
            if (brickCount > 0) {
                document.getElementById('model-name').textContent = filename;
                document.getElementById('brick-count').textContent = brickCount;
                brickStats.style.display = 'block';
                
                // Update the main info area
                modelInfo.innerHTML = `
                    <h3>🧱 LEGO 3D Viewer</h3>
                    <div id="brick-stats">
                        <strong>Current Model:</strong><br>
                        <span id="model-name">${filename}</span><br>
                        <span id="brick-count">${brickCount}</span> bricks
                    </div>
                `;
            } else {
                modelInfo.innerHTML = `
                    <h3>🧱 LEGO 3D Viewer</h3>
                    <p>Generate models below to see them here!</p>
                    <div id="brick-stats" style="display: none;">
                        <strong>Current Model:</strong><br>
                        <span id="model-name">-</span><br>
                        <span id="brick-count">0</span> bricks
                    </div>
                `;
            }
        }
        
        // Center camera on model
        function centerCameraOnModel() {
            if (!currentModel) return;
            
            const box = new THREE.Box3().setFromObject(currentModel);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            const maxDim = Math.max(size.x, size.y, size.z);
            const distance = maxDim * 2;
            
            camera.position.set(
                center.x + distance,
                center.y + distance,
                center.z + distance
            );
            
            controls.target.copy(center);
        }
        
        // Animation loop
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        
        // Window resize handler
        function onWindowResize() {
            const canvas = document.getElementById('three-canvas');
            camera.aspect = canvas.clientWidth / canvas.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
        }
        
        // Viewer control functions
        function clearScene() {
            if (currentModel) {
                scene.remove(currentModel);
                currentModel = null;
                
                // Update info display
                updateModelInfo('No model loaded', 0);
                
                // Reset dropdown selection
                const select = document.getElementById('modelDropdown');
                select.value = '';
                
                // Reset camera to default position
                resetCamera();
            }
        }
        
        function resetCamera() {
            camera.position.set(50, 50, 50);
            controls.target.set(0, 0, 0);
        }
        
        function toggleWireframe() {
            wireframeMode = !wireframeMode;
            if (currentModel) {
                currentModel.traverse((child) => {
                    if (child.isMesh) {
                        child.material.wireframe = wireframeMode;
                    }
                });
            }
        }
        
        function randomizeColors() {
            if (!currentModel) return;
            
            const colors = Object.values(LEGO_COLORS);
            currentModel.traverse((child) => {
                if (child.isMesh) {
                    const randomColor = colors[Math.floor(Math.random() * colors.length)];
                    child.material.color.setHex(randomColor);
                }
            });
        }
        
        // Model management
        async function refreshModelList() {
            try {
                const response = await fetch('/api/models');
                const data = await response.json();
                
                const select = document.getElementById('modelDropdown');
                select.innerHTML = '<option value="">Select a model to view...</option>';
                
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Failed to refresh models:', error);
            }
        }
        
        async function loadSelectedModel() {
            const select = document.getElementById('modelDropdown');
            const filename = select.value;
            
            if (!filename) {
                alert('Please select a model to load! 📂');
                return;
            }
            
            try {
                const response = await fetch(`/api/model-content/${filename}`);
                if (!response.ok) throw new Error('Failed to load model');
                
                const content = await response.text();
                loadModel(content, filename);
            } catch (error) {
                alert('Failed to load model: ' + error.message);
            }
        }
        // Generate LEGO model
        async function generateModel() {
            const prompt = document.getElementById('prompt').value.trim();
            const filename = document.getElementById('filename').value.trim();
            const seed = parseInt(document.getElementById('seed').value);
            
            if (!prompt) {
                alert('Please describe your LEGO creation! 🧱');
                return;
            }
            
            const result = document.getElementById('result');
            const button = document.querySelector('.generate-btn');
            
            // Show loading state
            button.disabled = true;
            button.innerHTML = '<span class="loading">🔄</span> Creating...';
            result.innerHTML = '<div class="result">🎨 BrickGPT is designing your creation...</div>';
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, filename, seed })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    result.innerHTML = `
                        <div class="result">
                            <h3>🎉 ${data.message}</h3>
                            <div class="stats-grid">
                                <div class="stat-item">
                                    <div class="stat-value">${data.stats.total_bricks}</div>
                                    <div class="stat-label">Bricks</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">${data.stats.generation_time}</div>
                                    <div class="stat-label">Time</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">${data.stats.estimated_cost}</div>
                                    <div class="stat-label">Cost</div>
                                </div>
                            </div>
                            <div class="download-links">
                                <a href="/api/download/${data.files.txt}">📄 Instructions</a>
                                <a href="/api/download/${data.files.ldr}">🧱 3D Model</a>
                            </div>
                            <div class="tip">
                                <strong>🎯 Success!</strong> Your LEGO model is now visible in the 3D viewer above!
                                ${data.note ? `<br><em>${data.note}</em>` : ''}
                            </div>
                        </div>
                    `;
                    
                    // Auto-load the new model in 3D viewer
                    setTimeout(() => {
                        refreshModelList();
                        setTimeout(() => {
                            loadNewModel(data.files.txt);
                        }, 500);
                    }, 500);
                } else {
                    result.innerHTML = `<div class="result error">❌ Error: ${data.error}</div>`;
                }
            } catch (error) {
                result.innerHTML = `<div class="result error">❌ Network error: ${error.message}</div>`;
            } finally {
                // Reset button
                button.disabled = false;
                button.innerHTML = '🚀 Generate';
            }
        }
        
        // Auto-load newly generated model
        async function loadNewModel(filename) {
            try {
                const response = await fetch(`/api/model-content/${filename}`);
                if (!response.ok) throw new Error('Failed to load model');
                
                const content = await response.text();
                loadModel(content, filename);
                
                // Update dropdown selection
                const select = document.getElementById('modelDropdown');
                select.value = filename;
            } catch (error) {
                console.error('Failed to auto-load model:', error);
            }
        }
        
        // Add keyboard shortcuts
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize 3D scene
            init3DScene();
            
            // Ctrl+Enter to generate
            document.getElementById('prompt').addEventListener('keydown', function(e) {
                if (e.ctrlKey && e.key === 'Enter') {
                    generateModel();
                }
            });
            
            // Auto-focus on prompt
            document.getElementById('prompt').focus();
            
            // Random seed button behavior
            document.getElementById('seed').addEventListener('click', function() {
                if (this.value == 42) {
                    this.value = Math.floor(Math.random() * 1000);
                }
            });
        });
    </script>
</body>
</html>
    """

@app.route('/api/generate', methods=['POST'])
def generate_model():
    """Generate a LEGO model from text description."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        filename = secure_filename(data.get('filename', 'model'))
        seed = data.get('seed', 42)
        
        if not prompt:
            return jsonify({'success': False, 'error': 'No prompt provided'})
        
        # Mock generation
        random.seed(seed)
        
        brick_count = random.randint(20, 60)
        colors = [0, 1, 2, 4, 6, 14, 15]
        brick_types = ['1x1', '1x2', '1x4', '2x2', '2x4']
        
        # Generate TXT content
        txt_content = f"# LEGO Model: {filename}\n"
        txt_content += f"# Generated from: {prompt}\n"
        txt_content += f"# Total bricks: {brick_count}\n\n"
        
        ldr_content = "0 LEGO Model\n0 Name: " + filename + "\n\n"
        
        for i in range(brick_count):
            x = random.randint(0, 20) * 8
            y = random.randint(0, 10) * 8  
            z = random.randint(0, 20) * 8
            color = random.choice(colors)
            brick_type = random.choice(brick_types)
            
            txt_content += f"Place {brick_type} brick at ({x}, {y}, {z}) with color {color}\n"
            
            # LDR format
            part_map = {'1x1': '3005.dat', '1x2': '3004.dat', '1x4': '3010.dat', 
                       '2x2': '3003.dat', '2x4': '3001.dat'}
            part = part_map.get(brick_type, '3001.dat')
            ldr_content += f"1 {color} {x} {y} {z} 1 0 0 0 1 0 0 0 1 {part}\n"
        
        # Save files
        txt_file = OUTPUT_FOLDER / f"{filename}.txt"
        ldr_file = OUTPUT_FOLDER / f"{filename}.ldr"
        
        with open(txt_file, 'w') as f:
            f.write(txt_content)
        
        with open(ldr_file, 'w') as f:
            f.write(ldr_content)
        
        return jsonify({
            'success': True,
            'message': f'Successfully generated "{filename}"',
            'files': {
                'txt': f"{filename}.txt",
                'ldr': f"{filename}.ldr"
            },
            'stats': {
                'total_bricks': brick_count,
                'generation_time': f"{random.uniform(2.1, 5.8):.1f}s",
                'estimated_cost': f"${random.randint(25, 120)}"
            },
            'note': "Demo version - Connect real BrickGPT for actual AI generation."
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/models', methods=['GET'])
def list_models():
    """Get list of available models."""
    try:
        models = []
        for file in OUTPUT_FOLDER.glob('*.txt'):
            models.append(file.name)
        for file in OUTPUT_FOLDER.glob('*.ldr'):
            if file.with_suffix('.txt').name not in models:
                models.append(file.name)
        
        return jsonify({'models': sorted(models)})
    except Exception as e:
        return jsonify({'models': [], 'error': str(e)})

@app.route('/api/model-content/<filename>')
def get_model_content(filename):
    """Get content of a specific model file."""
    try:
        filepath = OUTPUT_FOLDER / secure_filename(filename)
        if not filepath.exists():
            return "File not found", 404
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        return content, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return f"Error reading file: {str(e)}", 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a generated file."""
    try:
        filepath = OUTPUT_FOLDER / secure_filename(filename)
        if not filepath.exists():
            return "File not found", 404
        
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500

if __name__ == '__main__':
    print("🧱 Starting Simple Text-to-LEGO Generator...")
    print("📍 Server: http://localhost:5001")
    print("✨ Pure text-to-LEGO generation - clean and focused!")
    print("🔧 Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)