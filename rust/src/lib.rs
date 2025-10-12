use pyo3::prelude::*;
use std::f64::consts::PI;
// ✅ Importación del crate real 'wigners'
use wigners::wigner_3j; 


// REEMPLAZAR la función #[pymodule] actual con esta:
#[pymodule]
fn cosmic_vorticity(_py: Python, m: &PyModule) -> PyResult<()> {
    // Funciones originales
    m.add_function(wrap_pyfunction!(calcular_bispectro_triangular, m)?)?;
    m.add_function(wrap_pyfunction!(modelo_vorticidad_plasma, m)?)?;
    m.add_function(wrap_pyfunction!(estadisticas_no_gaussianas, m)?)?;

    // NUEVAS FUNCIONES PARA GALAXIAS
    m.add_function(wrap_pyfunction!(generar_imagen_png, m)?)?;
    m.add_function(wrap_pyfunction!(generar_reporte_html, m)?)?;
    m.add_function(wrap_pyfunction!(exportar_datos_visualizacion, m)?)?;
    m.add_function(wrap_pyfunction!(analizar_morfologia_galaxia, m)?)?;
    m.add_function(wrap_pyfunction!(calcular_patrones_lineas, m)?)?;

    Ok(())
}

#[pyfunction]
fn calcular_bispectro_triangular(
    modos_b: Vec<f32>,
    l_max: u16,
    configs: Vec<(u16, u16, u16)>
) -> PyResult<Vec<f32>> {
    let resultados: Vec<f32> = configs.iter()
        .map(|&(l1, l2, l3)| calcular_bispectro_config(&modos_b, l1, l2, l3, l_max))
        .collect();
    Ok(resultados)
}

#[pyfunction]
fn modelo_vorticidad_plasma(
    parametros: Vec<f32>,
    n_puntos: u16
) -> PyResult<Vec<f32>> {
    let resultado: Vec<f32> = (0..n_puntos).map(|i| {
        let x = i as f32 / n_puntos as f32 * 2.0 * PI as f32;
        parametros[0] * x.sin() * (-parametros[1] * x).exp()
    }).collect();
    Ok(resultado)
}

#[pyfunction]
fn estadisticas_no_gaussianas(datos: Vec<f32>) -> PyResult<Vec<f32>> {
    let n = datos.len() as f32;
    let media = datos.iter().sum::<f32>() / n;
    let varianza = datos.iter().map(|&x| (x - media).powi(2)).sum::<f32>() / n;
    let desviacion = varianza.sqrt();

    let asimetria = if desviacion > 0.0 {
        datos.iter().map(|&x| ((x - media) / desviacion).powi(3)).sum::<f32>() / n
    } else {
        0.0
    };

    let curtosis = if desviacion > 0.0 {
        datos.iter().map(|&x| ((x - media) / desviacion).powi(4)).sum::<f32>() / n - 3.0
    } else {
        0.0
    };

    Ok(vec![media, varianza, asimetria, curtosis])
}

fn condiciones_triangulo(l1: u16, l2: u16, l3: u16) -> bool {
    (l1 + l2 >= l3) && (l1 + l3 >= l2) && (l2 + l3 >= l1) &&
    (l1 + l2 + l3) % 2 == 0 
}

// 🚨 CORRECCIÓN CRÍTICA: Uso del crate 'wigners' y corrección de tipos
fn calcular_wigner_3j(l1: u16, l2: u16, l3: u16, m1: i16, m2: i16, m3: i16) -> f32 {
    
    // Filtros rápidos (Reglas de selección)
    if !condiciones_triangulo(l1, l2, l3) {
        return 0.0;
    }
    if m1 + m2 + m3 != 0 {
        return 0.0;
    }
    if m1.abs() > l1 as i16 || m2.abs() > l2 as i16 || m3.abs() > l3 as i16 {
        return 0.0;
    }

    // ✅ CORRECCIÓN DE TIPO: Usar u32 para l1, l2, l3. (Números cuánticos angulares no negativos)
    wigner_3j(
        l1 as u32, l2 as u32, l3 as u32, 
        m1 as i32, m2 as i32, m3 as i32
    ) as f32
}

// 🔧 CORRECCIÓN: Función 'obtener_modo' - Índice Óptimo (l² + m + l)
fn obtener_modo(modos_b: &[f32], l: u16, m: i16, _l_max: u16) -> f32 {
    let idx: usize = (l as usize).pow(2) + (m + l as i16) as usize;
    
    if idx < modos_b.len() { 
        modos_b[idx] 
    } else { 
        0.0 
    }
}


fn calcular_bispectro_config(
    modos_b: &[f32],
    l1: u16,
    l2: u16,
    l3: u16,
    l_max: u16
) -> f32 {
    if !condiciones_triangulo(l1, l2, l3) {
        return 0.0;
    }

    let mut suma = 0.0f32;
    let mut contador = 0u16;

    for m1 in (-(l1 as i16))..=(l1 as i16) {
        for m2 in (-(l2 as i16))..=(l2 as i16) {
            let m3 = -m1 - m2;
            if m3.abs() > l3 as i16 {
                continue;
            }

            let wigner = calcular_wigner_3j(l1, l2, l3, m1, m2, m3);
            let a1 = obtener_modo(modos_b, l1, m1, l_max);
            let a2 = obtener_modo(modos_b, l2, m2, l_max);
            let a3 = obtener_modo(modos_b, l3, m3, l_max);

            if wigner != 0.0 { 
                suma += wigner * a1 * a2 * a3;
                contador += 1;
            }
        }
    }

    if contador > 0 {
        let prefactor = ((2*l1+1) * (2*l2+1) * (2*l3+1)) as f32;
        let prefactor = (prefactor / (4.0 * PI as f32)).sqrt();
        prefactor * suma
    } else {
        0.0
    }
}

// Implementación de generación de imágenes y reportes (sin cambios funcionales)

#[pyfunction]
fn generar_imagen_png(
    datos: Vec<f32>,
    dimensiones: (u32, u32),
    nombre_archivo: String
) -> PyResult<()> {
    use std::fs::File;
    use std::io::BufWriter;

    let (ancho, alto) = dimensiones;
    let mut buffer = Vec::new();

    // Encabezado PNG básico 
    buffer.extend_from_slice(b"\x89PNG\r\n\x1a\n");

    // Generar imagen en escala de grises (8-bit RGBA)
    for y in 0..alto {
        for x in 0..ancho {
            let idx = (y * ancho + x) as usize;
            let valor = if idx < datos.len() {
                (datos[idx].clamp(0.0, 1.0) * 255.0) as u8 
            } else {
                0
            };
            buffer.push(valor);
            buffer.push(valor);
            buffer.push(valor); // RGB
            buffer.push(255);   // Alpha
        }
    }

    // Guardar archivo
    let file = File::create(nombre_archivo)?;
    let mut writer = BufWriter::new(file);
    std::io::Write::write_all(&mut writer, &buffer)?;

    Ok(())
}

#[pyfunction]
fn generar_reporte_html(
    resultados: Vec<f32>,
    mapa_intensidad: Vec<f32>,
    dimensiones: (u32, u32),
    nombre_archivo: String
) -> PyResult<()> {
    use std::fs::File;
    use std::io::Write;

    let mut html = String::new();

    // Cabecera HTML
    html.push_str("<!DOCTYPE html>
<html>
<head>
    <title>Análisis Vorticidad Galáctica</title>
    <style>
        .container { display: flex; flex-wrap: wrap; }
        .plot { margin: 10px; border: 1px solid #ccc; }
    </style>
</head>
<body>
    <h1>🌌 Análisis de Vorticidad en GS-z14</h1>
    <div class='container'>");

    // Generar SVG simple para el mapa de intensidad
    html.push_str("<div class='plot'>
    <h3>Mapa de Intensidad</h3>
    <svg width='300' height='300'>");

    let (ancho, alto) = dimensiones;
    for y in 0..alto {
        for x in 0..ancho {
            let idx = (y * ancho + x) as usize;
            if idx < mapa_intensidad.len() {
                let intensidad = (mapa_intensidad[idx].clamp(0.0, 1.0) * 255.0) as u8;
                html.push_str(&format!(
                    "<rect x='{}' y='{}' width='1' height='1' fill='rgb({},{},{})'/>",
                    x * 300 / ancho, y * 300 / alto, intensidad, intensidad, intensidad
                ));
            }
        }
    }

    html.push_str("</svg></div>");

    // Gráfica de resultados (Gráfico de barras simple)
    html.push_str("<div class='plot'>
    <h3>Métrica Vorticidad</h3>
    <svg width='400' height='200'>");

    let max_val = resultados.iter().fold(1.0f32, |a, &b| a.max(b));
    for (i, &valor) in resultados.iter().enumerate() {
        let x = i * 400 / resultados.len();
        let altura = (valor / max_val * 150.0) as u32;
        let color = if valor > 1.5 { "red" } else { "blue" };
        html.push_str(&format!(
            "<rect x='{}' y='{}' width='10' height='{}' fill='{}'/>",
            x, 200 - altura, altura, color
        ));
    }

    html.push_str("</svg></div>");

    // Cerrar HTML
    html.push_str("</div></body></html>");

    // Guardar archivo
    let mut file = File::create(nombre_archivo)?;
    file.write_all(html.as_bytes())?;

    Ok(())
}

#[pyfunction]
fn exportar_datos_visualizacion(
    mapa_intensidad: Vec<f32>,
    mapa_ratio: Vec<f32>,
    dimensiones: (u32, u32),
    resultados: Vec<f32>
) -> PyResult<String> {
    // Generar JSON para visualización externa
    let json_data = format!(r#"{{
        "dimensiones": [{}, {}],
        "mapa_intensidad": {:?},
        "mapa_ratio": {:?},
        "metricas_vorticidad": {:?},
        "ratio_promedio": {:.3},
        "conclusion": "{}"
    }}"#,
        dimensiones.0, dimensiones.1,
        mapa_intensidad,
        mapa_ratio,
        resultados,
        resultados.iter().sum::<f32>() / resultados.len() as f32,
        if resultados.iter().any(|&x| x > 1.5) {
            "POSIBLE_VORTICIDAD_DETECTADA"
        } else {
            "SIN_EVIDENCIA_FUERTE"
        }
    );

    Ok(json_data)
}

#[pyfunction]
fn analizar_morfologia_galaxia(
    mapa_intensidad: Vec<f32>,
    dimensiones: (u32, u32),
    umbral_snr: f32
) -> PyResult<Vec<f32>> {
    let (ancho, alto) = dimensiones;
    let mut resultados = Vec::new();

    // 1. Calcular centro de masa
    let mut suma_x = 0.0;
    let mut suma_y = 0.0;
    let mut suma_total = 0.0;

    for y in 0..alto {
        for x in 0..ancho {
            let idx = (y * ancho + x) as usize;
            let intensidad = mapa_intensidad[idx];
            if intensidad > umbral_snr {
                suma_x += x as f32 * intensidad;
                suma_y += y as f32 * intensidad;
                suma_total += intensidad;
            }
        }
    }

    let centro_x = suma_x / suma_total;
    let centro_y = suma_y / suma_total;
    resultados.push(centro_x);
    resultados.push(centro_y);

    // 2. Calcular elipticidad y orientación (Momentos de inercia)
    let mut mu_xx = 0.0;
    let mut mu_yy = 0.0;
    let mut mu_xy = 0.0; // Advertencia: variable 'mu_xy' nunca se usa

    for y in 0..alto {
        for x in 0..ancho {
            let idx = (y * ancho + x) as usize;
            let intensidad = mapa_intensidad[idx];
            if intensidad > umbral_snr {
                let dx = x as f32 - centro_x;
                let dy = y as f32 - centro_y;
                mu_xx += dx * dx * intensidad;
                mu_yy += dy * dy * intensidad;
                mu_xy += dx * dy * intensidad;
            }
        }
    }

    let elipticidad = (mu_xx - mu_yy) / (mu_xx + mu_yy);
    resultados.push(elipticidad.abs());

    // 3. Métrica simple de patrón rotacional
    let patron_rotacional = calcular_patron_rotacional(&mapa_intensidad, dimensiones);
    resultados.push(patron_rotacional);

    Ok(resultados)
}

#[pyfunction]
fn calcular_patrones_lineas(
    mapa_oiii: Vec<f32>,
    mapa_cii: Vec<f32>,
    dimensiones: (u32, u32)
) -> PyResult<Vec<f32>> {
    let (ancho, alto) = dimensiones;
    let mut resultados = Vec::new();

    // 1. Calcular ratio [OIII]/[CII] pixel a pixel
    let mut mapa_ratio = Vec::new();
    let mut ratios_validos = Vec::new();

    for i in 0..mapa_oiii.len() {
        if i < mapa_cii.len() && mapa_cii[i] > 0.0 {
            let ratio = mapa_oiii[i] / mapa_cii[i];
            mapa_ratio.push(ratio);
            if ratio.is_finite() {
                ratios_validos.push(ratio);
            }
        } else {
            mapa_ratio.push(0.0);
        }
    }

    // 2. Aplicar bispectro adaptado al mapa de ratios
    let configs = vec![(2, 2, 2), (3, 3, 3), (2, 3, 4)];
    let bispectro_resultados = calcular_bispectro_adaptado_2d(&mapa_ratio, ancho, alto, configs);

    resultados.extend(bispectro_resultados);

    // 3. Calcular estadísticas del ratio
    if !ratios_validos.is_empty() {
        let ratio_promedio: f32 = ratios_validos.iter().sum::<f32>() / ratios_validos.len() as f32;
        resultados.push(ratio_promedio);

        let ratio_max = ratios_validos.iter().fold(0.0f32, |a, &b| a.max(b));
        resultados.push(ratio_max);
    }

    Ok(resultados)
}

// Función auxiliar para patrón rotacional
fn calcular_patron_rotacional(mapa: &[f32], dimensiones: (u32, u32)) -> f32 {
    let (ancho, alto) = dimensiones;
    let mut asimetria_angular = 0.0;

    // Análisis simple de simetría angular, asumiendo centro en (ancho/2, alto/2)
    for y in 0..alto {
        for x in 0..ancho {
            let idx = (y * ancho + x) as usize;
            if idx < mapa.len() {
                let dx = x as f32 - ancho as f32 / 2.0;
                let dy = y as f32 - alto as f32 / 2.0;
                let angulo = dy.atan2(dx);
                asimetria_angular += mapa[idx] * angulo.sin();
            }
        }
    }

    asimetria_angular.abs()
}

// Bispectro adaptado para mapas 2D - AÚN PLACEHOLDER
fn calcular_bispectro_adaptado_2d(
    mapa: &[f32],
    ancho: u32,
    alto: u32,
    configs: Vec<(u32, u32, u32)>
) -> Vec<f32> {
    // ⚠️ Advertencia: ESTE ES UN PLACEHOLDER. Debe ser implementado para un análisis 2D serio.
    // Ignorando temporalmente las variables no utilizadas para evitar warnings aquí.
    let _ = (mapa, ancho, alto); 

    configs.iter().map(|&(l1, l2, l3)| {
        (l1 + l2 + l3) as f32 * 0.1 
    }).collect()
}
