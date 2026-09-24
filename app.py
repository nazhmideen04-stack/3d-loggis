# app.py (Обновленный фрагмент THREE.JS для легенды)
# Замените старый скрипт THREE.JS в html_template на этот обновленный,
# который динамически меняет цвета шкалы в зависимости от выбранного типа.

import streamlit as st
import json

# ... (Весь код Streamlit, CSS и навигации остается прежним) ...

# Замените html_template или только THREE.JS скрипт:

threejs_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #0A0E17;
            font-family: 'Chakra Petch', sans-serif;
        }}
        #canvas-container {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}
        /* ... (Старый CSS для легенды) ... */
        #color-legend {{
            position: absolute;
            top: 24px;
            right: 28px;
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(10, 14, 23, 0.9);
            padding: 14px 16px;
            border: 1px solid rgba(0, 200, 230, 0.45);
            box-shadow: 0 0 18px rgba(0, 200, 230, 0.15);
            border-radius: 6px;
            z-index: 90;
            user-select: none;
        }}
        #legend-title {{
            color: #00E5FF;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 8px;
            text-transform: none !important;
        }}
        .legend-bar-container {{
            display: flex;
            align-items: stretch;
            height: 240px;
        }}
        #legend-bar {{
            width: 20px;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            margin-right: 10px;
        }}
        /* ... (Остальной CSS) ... */
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js"></script>
</head>
<body>
    <div id="canvas-container">
        <!-- ... (Загрузчик и HUD) ... -->
        <div id="color-legend">
            <div id="legend-title">--</div>
            <div class="legend-bar-container">
                <div id="legend-bar"></div>
                <div class="legend-labels">
                    <span id="lbl-max">--</span>
                    <span id="lbl-mid">--</span>
                    <span id="lbl-min">--</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const payload = {json_payload};
        const modelB64 = "{model_b64}";
        
        const legendBar = document.getElementById('legend-bar');
        const legendTitle = document.getElementById('legend-title');
        
        // --- ОБНОВЛЕННЫЕ ГРАДИЕНТЫ ДЛЯ КАЖДОГО ТИПА ---
        // Эти цвета используются и в 3D, и в легенде

        const hoopStops = [
            new THREE.Color("#001144"), // Очень глубокий синий (мин)
            new THREE.Color("#00E5FF"), // Яркий циан
            new THREE.Color("#00FF44"), // Чистый зеленый
            new THREE.Color("#FFE600")  // Желтый (макс)
        ];

        const axialStops = [
            new THREE.Color("#00FF44"), // Зеленый (мин)
            new THREE.Color("#FFE600"), // Желтый
            new THREE.Color("#FF8800"), // Оранжевый
            new THREE.Color("#FF0033")  // Красный (макс)
        ];

        const tempStops = [
            new THREE.Color("#330066"), // Глубокий фиолетовый (холодно)
            new THREE.Color("#00E5FF"), // Циан
            new THREE.Color("#FFFFFF"), // Белый (комфортно)
            new THREE.Color("#FF0033")  // Яркий красный (горячо)
        ];

        // --- ОБНОВЛЕНИЕ ЛЕГЕНДЫ ---
        let currentStops = hoopStops;
        let gradientStr = "";

        if (payload.comp === "axial") {{
            currentStops = axialStops;
            legendTitle.innerText = "Axial [µm/m]";
            gradientStr = "linear-gradient(to bottom, #FF0033, #FF8800, #FFE600, #00FF44)";
        }} else if (payload.comp === "temp") {{
            currentStops = tempStops;
            legendTitle.innerText = "Temp [°C]";
            gradientStr = "linear-gradient(to bottom, #FF0033, #FFFFFF, #00E5FF, #330066)";
        }} else {{
            // hoop / default
            legendTitle.innerText = "Hoop [µm/m]";
            gradientStr = "linear-gradient(to bottom, #FFE600, #00FF44, #00E5FF, #001144)";
        }}
        
        // Применяем CSS градиент к шкале легенды, соответствующий 3D сцене
        legendBar.style.background = gradientStr;

        // ... (Весь остальной код Three.js для рендеринга и интерполяции остается без изменений,
        // убедитесь, что функция getColorForValue использует currentStops) ...

        function getColorForValue(val, clim) {{
            if (val === undefined || isNaN(val)) return new THREE.Color(0x334455);
            const min = clim[0], max = clim[1];
            let t = (val - min) / ((max - min) || 1.0);
            t = Math.max(0, Math.min(1, t));

            // Функция интерполяции должна использовать dynamicStops (или currentStops)
            t = Math.max(0, Math.min(1, t));
            const scaled = t * (currentStops.length - 1);
            const idx = Math.floor(scaled);
            const fract = scaled - idx;
            if (idx >= currentStops.length - 1) return currentStops[currentStops.length - 1].clone();
            const c = new THREE.Color();
            c.lerpColors(currentStops[idx], currentStops[idx + 1], fract);
            return c;
        }}

        // ... (Весь остальной код анимации и загрузки) ...
    </script>
</body>
</html>
"""

# ... (Остальной код Streamlit) ...
