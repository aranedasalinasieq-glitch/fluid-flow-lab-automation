from pathlib import Path
import argparse
from src.io_excel import load_input
from src.analyze import analyze
from src.report import write_results, create_plots

def main():
    ap=argparse.ArgumentParser(description="Automatización de laboratorio de escurrimiento de fluidos")
    ap.add_argument("excel", help="Archivo Excel de entrada")
    ap.add_argument("-o","--output",default="output/resultados_escurrimiento.xlsx")
    ap.add_argument("--plots",default="graficos")
    args=ap.parse_args()
    data=load_input(args.excel)
    result=analyze(data)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    write_results(result,args.output)
    plots=create_plots(result,args.plots)
    print(f"Resultados: {args.output}")
    for p in plots: print(f"Gráfico: {p}")
    print(f"Calibración: Q = {result['calibration'].a:.6e}·sqrt(ΔP) + {result['calibration'].b:.6e}; R²={result['calibration'].r2:.5f}")
    if result["warnings"]:
        print("Advertencias:")
        for w in result["warnings"]: print(" -",w)

if __name__=="__main__":
    main()
