# Fluid Flow Lab Automation

Herramienta en Python para automatizar el procesamiento de un laboratorio académico de **escurrimiento de fluidos / pérdidas de carga y medidores de flujo**.

## Qué automatiza

- Calibración experimental de placa orificio desde lecturas de manómetro en U, masa y tiempo.
- Conversión de lecturas manométricas a ΔP.
- Ajuste de calibración `Q = a·sqrt(ΔP) + b` y cálculo de R².
- Caudal, área, velocidad, Reynolds y clasificación de régimen.
- Factor de fricción de Darcy: `64/Re` en laminar y Colebrook-White en turbulento.
- Pérdidas experimentales y Darcy-Weisbach en cañerías.
- K y L/D experimental en accesorios, con error frente a referencia opcional.
- Densidad del aire por gas ideal, velocidad local con Pitot, perfiles de velocidad y Mach.
- Velocidad media aritmética y estimación por integración trapezoidal del perfil.
- Advertencias por datos fuera del rango de calibración o condiciones problemáticas.
- Excel de resultados y gráficos PNG.

## Uso

```bash
pip install -r requirements.txt
python main.py entrada_laboratorio_escurrimiento.xlsx
```

Salida predeterminada:

- `output/resultados_escurrimiento.xlsx`
- `graficos/calibracion_Q_DeltaP.png`
- `graficos/perfil_pitot.png`

## Principio de diseño

El Excel de entrada contiene **datos primarios observables**. Las variables derivables (Q, ΔP, v, Re, f_D, K, L/D, Mach, etc.) se calculan en Python.

## Notas metodológicas

El programa usa el factor de **Darcy** de forma explícita. No mezcla el factor de Fanning con `4f`.
La calibración se representa en un gráfico Q–ΔP, pero el ajuste implementado respeta la dependencia física aproximada de una placa orificio: `Q ∝ sqrt(ΔP)`.
