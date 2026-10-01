from __future__ import annotations
import math
from collections import defaultdict
from .core import *

def _p(params, name, default=None):
    v = params.get(name, default)
    if v is None:
        raise ValueError(f"Falta parámetro: {name}")
    return float(v)

def roughness_for(material, params, override=None):
    if override not in (None, ""):
        return float(override)
    m = str(material or "").strip().lower()
    if "acero" in m:
        return _p(params, "Rugosidad acero comercial")
    if "cobre" in m:
        return _p(params, "Rugosidad cobre")
    raise ValueError(f"No hay rugosidad definida para material '{material}'. Añádala como override.")

def analyze(data):
    p = data["params"]
    g = _p(p, "Gravedad", 9.80665)
    rho_hg = _p(p, "Densidad mercurio", 13600)
    rho_w = _p(p, "Densidad agua (modo reproducción)", 998)
    mu_w = _p(p, "Viscosidad agua (modo reproducción)", 0.001)

    warnings = []
    cal_rows = []
    for r in data["calibracion"]:
        if r.get("H1 placa") is None:
            continue
        dh, dp = manometer_dp(r["H1 placa"], r["H2 placa"], r["Unidad H"], rho_hg, rho_w, g)
        q = float(r["Masa recolectada"])/(rho_w*float(r["Tiempo"]))
        cal_rows.append({**r, "DeltaH_m": dh, "DeltaP_Pa": dp, "Q_m3s": q})
        if dp < 1e-9 and q > 1e-8:
            warnings.append("Calibración: ΔP≈0 con Q distinto de cero; revisar offset experimental.")
    calibration = fit_orifice([r["DeltaP_Pa"] for r in cal_rows], [r["Q_m3s"] for r in cal_rows])
    if calibration.r2 < 0.98:
        warnings.append(f"Calibración: R²={calibration.r2:.4f}; revisar dispersión, rango u offset.")

    pipe_rows = []
    for r in data["canerias"]:
        if r.get("ID") is None:
            continue
        D = length_to_m(r["D interno"], r["Unidad D"])
        L = length_to_m(r["L entre tomas"], r["Unidad L"])
        _, dp_loss = manometer_dp(r["H1 pérdida"], r["H2 pérdida"], r["Unidad H pérdida"], rho_hg, rho_w, g)
        _, dp_plate = manometer_dp(r["H1 placa"], r["H2 placa"], r["Unidad H placa"], rho_hg, rho_w, g)
        q = calibration.q(dp_plate)
        A = area_circle(D); v = q/A
        Re = reynolds(rho_w, v, D, mu_w)
        eps = roughness_for(r.get("Material"), p, r.get("Rugosidad m"))
        f = darcy_factor(Re, eps/D)
        ev_exp = dp_loss/rho_w
        ev_teo = f*(L/D)*(v*v/2)
        if dp_plate < calibration.dp_min or dp_plate > calibration.dp_max:
            warnings.append(f"Cañería {r['ID']}: ΔP de placa fuera del rango de calibración.")
        if flow_regime(Re) == "transición":
            warnings.append(f"Cañería {r['ID']}: flujo en zona de transición (Re={Re:.0f}).")
        pipe_rows.append({
            **r, "D_m":D, "L_m":L, "DeltaP_placa_Pa":dp_plate, "Q_m3s":q, "Area_m2":A,
            "v_ms":v, "Re":Re, "Regimen":flow_regime(Re), "Rugosidad_m":eps,
            "Rugosidad_relativa":eps/D, "f_Darcy":f, "DeltaP_perdida_Pa":dp_loss,
            "Ev_exp_m2s2":ev_exp, "Ev_teo_m2s2":ev_teo,
            "Error_pct":pct_error(ev_exp, ev_teo), "Desviacion_pct":signed_deviation(ev_exp, ev_teo)
        })

    acc_rows = []
    for r in data["accesorios"]:
        if r.get("ID") is None:
            continue
        D = length_to_m(r["D interno"], r["Unidad D"])
        _, dp_loss = manometer_dp(r["H1 accesorio"], r["H2 accesorio"], r["Unidad H accesorio"], rho_hg, rho_w, g)
        _, dp_plate = manometer_dp(r["H1 placa"], r["H2 placa"], r["Unidad H placa"], rho_hg, rho_w, g)
        q = calibration.q(dp_plate); A=area_circle(D); v=q/A
        Re=reynolds(rho_w,v,D,mu_w)
        material = r.get("Material") or "Acero comercial"
        eps=roughness_for(material,p,r.get("Rugosidad m"))
        f=darcy_factor(Re,eps/D)
        ev=dp_loss/rho_w
        K=2*ev/(v*v)
        LD=K/f
        ref=r.get("L/D referencia")
        ref=float(ref) if ref not in (None,"") else math.nan
        if dp_plate < calibration.dp_min or dp_plate > calibration.dp_max:
            warnings.append(f"Accesorio {r['ID']}: ΔP de placa fuera del rango de calibración.")
        acc_rows.append({
            **r, "Material_usado":material, "D_m":D, "DeltaP_placa_Pa":dp_plate, "Q_m3s":q,
            "Area_m2":A, "v_ms":v, "Re":Re, "Regimen":flow_regime(Re), "Rugosidad_m":eps,
            "f_Darcy":f, "DeltaP_accesorio_Pa":dp_loss, "Ev_exp_m2s2":ev, "K_exp":K,
            "L_D_exp":LD, "L_D_ref":ref, "Error_LD_pct":pct_error(LD,ref) if not math.isnan(ref) else math.nan,
            "Desviacion_LD_pct":signed_deviation(LD,ref) if not math.isnan(ref) else math.nan
        })

    Tair = _p(p, "Temperatura aire", 20)+273.15
    Patm = _p(p, "Presión atmosférica",101325)
    Mair = _p(p, "Masa molar aire seco",0.02897)
    Ru = _p(p, "Constante universal gases Ru",8.314462618)
    Rair = _p(p, "Constante específica aire",287.05)
    gamma = _p(p, "Gamma aire",1.4)
    Cpitot = _p(p, "Coeficiente Pitot",1.0)
    rho_air = air_density(Patm,Tair,Mair,Ru)
    a_sound = speed_of_sound(gamma,Rair,Tair)

    pitot_rows=[]; groups=defaultdict(list)
    for r in data["pitot"]:
        if r.get("Posición") is None:
            continue
        pos=length_to_m(r["Posición"],r["Unidad posición"])
        dhavg=(float(r["ΔH toma 1"])+float(r["ΔH toma 2"]))/2
        dp=water_manometer_dp(dhavg,r["Unidad ΔH"],rho_w,rho_air,g)
        v=pitot_velocity(dp,rho_air,Cpitot)
        rec={**r,"Posicion_m":pos,"DeltaH_prom":dhavg,"DeltaP_Pa":dp,"rho_aire_kgm3":rho_air,"v_local_ms":v}
        pitot_rows.append(rec); groups[float(r["Apertura válvula"])].append(rec)

    pitot_summary=[]
    for angle, rows in sorted(groups.items()):
        xs=[x["Posicion_m"] for x in rows]; vs=[x["v_local_ms"] for x in rows]
        v_arith=sum(vs)/len(vs)
        v_trap=trapz_mean_velocity(xs,vs)
        pitot_summary.append({
            "Apertura_deg":angle, "n":len(rows), "v_media_arit_ms":v_arith,
            "v_media_trapecio_ms":v_trap, "a_sonido_ms":a_sound,
            "Mach_arit":v_arith/a_sound, "Mach_trapecio":v_trap/a_sound
        })
    return {
        "calibration": calibration, "calibration_rows":cal_rows, "pipes":pipe_rows,
        "accessories":acc_rows, "pitot":pitot_rows, "pitot_summary":pitot_summary,
        "warnings":warnings, "rho_air":rho_air, "speed_sound":a_sound
    }
