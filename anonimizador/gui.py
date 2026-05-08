"""Interfaz gráfica (Tkinter) del anonimizador de CFDI.

Sencilla a propósito: selectores de carpetas, casillas de opciones, botón de
ejecutar y barra de progreso. El trabajo pesado corre en un hilo aparte y se
comunica con la UI por una cola (Tkinter no es seguro entre hilos).
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .procesador import Procesador

APP_TITULO = "CFDI Anonymizer — Anonimizador de CFDI"


class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=12)
        self.master = master
        master.title(APP_TITULO)
        master.minsize(680, 540)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.cola: queue.Queue = queue.Queue()
        self._construir()
        self.after(100, self._vaciar_cola)

    # ------------------------------------------------------------------
    def _construir(self) -> None:
        self.var_origen = tk.StringVar()
        self.var_destino = tk.StringVar()
        self.var_mapeo = tk.StringVar()
        self.var_seed = tk.StringVar()
        self.var_keep = tk.BooleanVar(value=True)
        self.var_boveda = tk.BooleanVar(value=False)
        self.var_jitter = tk.BooleanVar(value=False)
        self.var_revertir = tk.BooleanVar(value=False)

        fila = 0
        self._fila_carpeta("Carpeta de origen (XML reales):", self.var_origen, fila); fila += 1
        self._fila_carpeta("Carpeta de destino (mocks):", self.var_destino, fila); fila += 1
        self._fila_carpeta("Carpeta de mapeo/semilla (mapeo.sqlite):", self.var_mapeo, fila,
                           ayuda="Opcional; por defecto = destino"); fila += 1

        # Opciones
        ops = ttk.LabelFrame(self, text="Opciones", padding=8)
        ops.grid(row=fila, column=0, columnspan=3, sticky="ew", pady=(8, 4))
        ops.columnconfigure(0, weight=1)
        ops.columnconfigure(1, weight=1)
        ttk.Checkbutton(ops, text="Conservar una copia de los originales",
                        variable=self.var_keep).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(ops, text="Usar estructura Bóveda en el destino",
                        variable=self.var_boveda).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(ops, text="Alterar salarios de Nómina (jitter)",
                        variable=self.var_jitter).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(ops, text="Modo revertir (reconstruir reales)",
                        variable=self.var_revertir,
                        command=self._toggle_revertir).grid(row=1, column=1, sticky="w")
        fila += 1

        sf = ttk.Frame(self)
        sf.grid(row=fila, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        ttk.Label(sf, text="Semilla (seed, opcional):").grid(row=0, column=0, sticky="w")
        ttk.Entry(sf, textvariable=self.var_seed, width=14).grid(row=0, column=1, sticky="w", padx=6)
        fila += 1

        # Botón ejecutar + progreso
        self.btn = ttk.Button(self, text="Ejecutar", command=self._ejecutar)
        self.btn.grid(row=fila, column=0, columnspan=3, sticky="ew", pady=(8, 4))
        fila += 1
        self.barra = ttk.Progressbar(self, mode="determinate")
        self.barra.grid(row=fila, column=0, columnspan=3, sticky="ew")
        fila += 1
        self.estado = ttk.Label(self, text="Listo.")
        self.estado.grid(row=fila, column=0, columnspan=3, sticky="w", pady=(2, 4))
        fila += 1

        # Log
        self.rowconfigure(fila, weight=1)
        self.log = tk.Text(self, height=12, wrap="none")
        self.log.grid(row=fila, column=0, columnspan=3, sticky="nsew")
        sb = ttk.Scrollbar(self, command=self.log.yview)
        sb.grid(row=fila, column=3, sticky="ns")
        self.log.configure(yscrollcommand=sb.set, state="disabled")

    def _fila_carpeta(self, etiqueta: str, var: tk.StringVar, fila: int,
                      ayuda: str | None = None) -> None:
        ttk.Label(self, text=etiqueta).grid(row=fila, column=0, sticky="w", pady=2)
        ent = ttk.Entry(self, textvariable=var)
        ent.grid(row=fila, column=1, sticky="ew", padx=6)
        ttk.Button(self, text="Examinar…",
                   command=lambda: self._elegir_carpeta(var)).grid(row=fila, column=2)
        if ayuda:
            ent.insert(0, "")

    @staticmethod
    def _elegir_carpeta(var: tk.StringVar) -> None:
        d = filedialog.askdirectory()
        if d:
            var.set(d)

    def _toggle_revertir(self) -> None:
        rev = self.var_revertir.get()
        self.btn.configure(text="Revertir" if rev else "Ejecutar")

    # ------------------------------------------------------------------
    def _log(self, msg: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _ejecutar(self) -> None:
        origen = self.var_origen.get().strip()
        destino = self.var_destino.get().strip()
        if not origen or not Path(origen).is_dir():
            messagebox.showerror(APP_TITULO, "Selecciona una carpeta de origen válida.")
            return
        if not destino:
            messagebox.showerror(APP_TITULO, "Selecciona una carpeta de destino.")
            return
        seed = None
        if self.var_seed.get().strip():
            try:
                seed = int(self.var_seed.get().strip())
            except ValueError:
                messagebox.showerror(APP_TITULO, "La semilla debe ser un número entero.")
                return

        self.btn.configure(state="disabled")
        self.barra.configure(value=0)
        self.estado.configure(text="Procesando…")
        cfg = dict(
            origen=origen, destino=destino,
            mapeo=self.var_mapeo.get().strip() or None,
            seed=seed, keep=self.var_keep.get(), boveda=self.var_boveda.get(),
            jitter=self.var_jitter.get(), revertir=self.var_revertir.get(),
        )
        threading.Thread(target=self._trabajar, args=(cfg,), daemon=True).start()

    def _trabajar(self, cfg: dict) -> None:
        try:
            db_dir = cfg["mapeo"] or cfg["destino"]
            proc = Procesador(
                cfg["destino"], db_dir=db_dir, seed=cfg["seed"],
                jitter_salarios=cfg["jitter"], usar_boveda=cfg["boveda"],
                keep_originales=cfg["keep"],
            )

            def progreso(i, n, nombre):
                self.cola.put(("progreso", i, n, nombre))

            if cfg["revertir"]:
                res = proc.revertir_carpeta(cfg["origen"], cfg["destino"], progreso)
            else:
                res = proc.procesar_carpeta(cfg["origen"], progreso)
            proc.close()
            self.cola.put(("fin", res, cfg["revertir"]))
        except Exception as e:  # noqa: BLE001
            self.cola.put(("error", f"{type(e).__name__}: {e}"))

    def _vaciar_cola(self) -> None:
        try:
            while True:
                msg = self.cola.get_nowait()
                tipo = msg[0]
                if tipo == "progreso":
                    _, i, n, nombre = msg
                    self.barra.configure(maximum=n, value=i)
                    self.estado.configure(text=f"[{i}/{n}] {nombre}")
                    self._log(f"[{i}/{n}] {nombre}")
                elif tipo == "fin":
                    _, res, era_revertir = msg
                    verbo = "Revertidos" if era_revertir else "Enmascarados"
                    self.estado.configure(
                        text=f"{verbo}: {res.exitosos}/{res.total} | errores: {len(res.errores)}")
                    self._log(f"--- {verbo}: {res.exitosos}/{res.total} ---")
                    for nombre, err in res.errores:
                        self._log(f"  ERROR {nombre}: {err}")
                    self.btn.configure(state="normal")
                elif tipo == "error":
                    self.estado.configure(text="Error.")
                    self._log("ERROR: " + msg[1])
                    messagebox.showerror(APP_TITULO, msg[1])
                    self.btn.configure(state="normal")
        except queue.Empty:
            pass
        self.after(100, self._vaciar_cola)


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
