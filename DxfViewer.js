import React, { useState, useRef, useEffect } from 'react';
import DxfParser from 'dxf-parser';

const DxfViewer = () => {
    const canvasRef = useRef(null);
    const [fileData, setFileData] = useState(null);
    const [fileName, setFileName] = useState('');

    // Dosya Yükleme İşleyicisi
    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            setFileName(file.name);
            const reader = new FileReader();
            reader.onload = (event) => {
                const parser = new DxfParser();
                try {
                    const dxf = parser.parseSync(event.target.result);
                    setFileData(dxf);
                } catch (err) {
                    console.error('DXF parse hatası:', err);
                }
            };
            reader.readAsText(file);
        }
    };

    // Çizim ve Görselleştirme Fonksiyonu (REVİZE EDİLEN KISIM)
    useEffect(() => {
        if (!fileData || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // 1. Arka Planı Temizle ve Koyu Renk Yap (İSTEK: Koyu Mod)
        ctx.fillStyle = '#111827'; 
        ctx.fillRect(0, 0, width, height);
        
        // 2. Çizgi Stili (İSTEK: Beyaz Çizgiler)
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 1;

        // --- ÖLÇEKLEME MANTIĞI (Parçayı ekrana sığdırmak için) ---
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        const updateBounds = (x, y) => {
            if (x < minX) minX = x;
            if (y < minY) minY = y;
            if (x > maxX) maxX = x;
            if (y > maxY) maxY = y;
        };

        // Bounding Box Hesapla
        fileData.entities.forEach(entity => {
            if (entity.type === 'LINE') {
                entity.vertices.forEach(v => updateBounds(v.x, v.y));
            } else if (entity.type === 'CIRCLE' || entity.type === 'ARC') {
                updateBounds(entity.center.x - entity.radius, entity.center.y - entity.radius);
                updateBounds(entity.center.x + entity.radius, entity.center.y + entity.radius);
            } else if (entity.type === 'LWPOLYLINE' || entity.type === 'POLYLINE') {
                entity.vertices.forEach(v => updateBounds(v.x, v.y));
            }
        });

        // Eğer çizim boşsa hata vermesin
        if (minX === Infinity) return;

        const dxfWidth = maxX - minX;
        const dxfHeight = maxY - minY;
        const scaleX = (width - 40) / dxfWidth;   // 40px padding
        const scaleY = (height - 40) / dxfHeight;
        const scale = Math.min(scaleX, scaleY);   // En-boy oranını koru

        const centerX = (width - dxfWidth * scale) / 2;
        const centerY = (height - dxfHeight * scale) / 2;

        // Koordinat Dönüştürücü Helper (Y ekseni Canvas'ta terstir)
        const toScreenX = (x) => (x - minX) * scale + centerX;
        const toScreenY = (y) => height - ((y - minY) * scale + centerY); // Y'yi ters çevir (Flip Y)

        // --- ÇİZİM DÖNGÜSÜ ---
        ctx.beginPath();
        fileData.entities.forEach(entity => {
            
            // TİP 1: LINE (Düz Çizgi)
            if (entity.type === 'LINE') {
                ctx.moveTo(toScreenX(entity.vertices[0].x), toScreenY(entity.vertices[0].y));
                ctx.lineTo(toScreenX(entity.vertices[1].x), toScreenY(entity.vertices[1].y));
            }
            
            // TİP 2: CIRCLE (Daire)
            else if (entity.type === 'CIRCLE') {
                ctx.moveTo(toScreenX(entity.center.x) + entity.radius * scale, toScreenY(entity.center.y));
                ctx.arc(
                    toScreenX(entity.center.x),
                    toScreenY(entity.center.y),
                    entity.radius * scale,
                    0,
                    2 * Math.PI
                );
            }

            // TİP 3: ARC (Yay - EKSİK OLAN KISIM EKLENDİ)
            else if (entity.type === 'ARC') {
                // DXF açıları derecedir, radyana çevir.
                // Canvas Y ekseni ters olduğu için açılar da ters mantıkla işleyebilir,
                // ancak basit görselleştirme için standart dönüşüm genellikle yeterlidir.
                const startAngle = -entity.startAngle * (Math.PI / 180); 
                const endAngle = -entity.endAngle * (Math.PI / 180);
                
                ctx.moveTo(
                    toScreenX(entity.center.x) + Math.cos(startAngle) * entity.radius * scale,
                    toScreenY(entity.center.y) + Math.sin(startAngle) * entity.radius * scale
                );
                
                ctx.arc(
                    toScreenX(entity.center.x),
                    toScreenY(entity.center.y),
                    entity.radius * scale,
                    startAngle,
                    endAngle,
                    true // Counter-clockwise (Y flip olduğu için yönü ters aldık)
                );
            }

            // TİP 4: LWPOLYLINE (Birleşik Çizgi - EKSİK OLAN KISIM EKLENDİ)
            else if (entity.type === 'LWPOLYLINE' || entity.type === 'POLYLINE') {
                if (entity.vertices && entity.vertices.length > 0) {
                    ctx.moveTo(toScreenX(entity.vertices[0].x), toScreenY(entity.vertices[0].y));
                    for (let i = 1; i < entity.vertices.length; i++) {
                        ctx.lineTo(toScreenX(entity.vertices[i].x), toScreenY(entity.vertices[i].y));
                    }
                    if (entity.shape) { // Kapalı şekil mi?
                        ctx.lineTo(toScreenX(entity.vertices[0].x), toScreenY(entity.vertices[0].y));
                    }
                }
            }
        });
        ctx.stroke();

    }, [fileData]);

    return (
        <div className="flex flex-col items-center p-4">
            <div className="mb-4 w-full max-w-md">
                <label className="block text-sm font-medium text-gray-700 mb-2">DXF Dosyası Seç</label>
                <div className="flex items-center justify-center w-full">
                    <label className="flex flex-col w-full h-32 border-4 border-dashed hover:bg-gray-100 hover:border-gray-300">
                        <div className="flex flex-col items-center justify-center pt-7">
                            <p className="pt-1 text-sm tracking-wider text-gray-400 group-hover:text-gray-600">
                                {fileName || "Dosya seçin veya sürükleyin"}
                            </p>
                        </div>
                        <input type="file" accept=".dxf" className="opacity-0" onChange={handleFileUpload} />
                    </label>
                </div>
            </div>

            {/* CANVAS ALANI */}
            <canvas 
                ref={canvasRef} 
                width={600} 
                height={500} 
                className="border rounded shadow-lg"
                style={{ backgroundColor: '#111827' }} // CSS yedeği
            />
        </div>
    );
};

export default DxfViewer;
