from fastapi import FastAPI                                                                                           
  from bs4 import BeautifulSoup
  import requests                                                                                                       
  import unicodedata
  import re
  import os

  app = FastAPI()

  directorio = []

  def limpiar(texto):
      texto = unicodedata.normalize("NFD", texto)
      texto = re.sub(r"[\u0300-\u036f]", "", texto)
      return texto.lower().strip()

  def cargar_directorio():
      global directorio
      soup = BeautifulSoup(
          requests.get("https://www.hulihealth.com/es/doctor").text, "html.parser"
      )
      directorio = []
      for link in soup.find_all("a", href=True):
          href = link["href"]
          if "/es/doctor/" in href and href not in ["/es/doctor", "/es/doctor/"]:
              nombre = link.get_text(strip=True)
              if nombre:
                  directorio.append({
                      "nombre": nombre,
                      "nombre_limpio": limpiar(nombre),
                      "url": "https://www.hulihealth.com" + href if href.startswith("/") else href,
                  })

  @app.on_event("startup")
  def startup():
      cargar_directorio()

  @app.get("/")
  def inicio():
      return {"status": "ok", "doctores_cargados": len(directorio)}

  @app.get("/buscar")
  def buscar(nombre: str):
      nombre_limpio = limpiar(nombre)
      resultados = [
          d for d in directorio
          if nombre_limpio in d["nombre_limpio"]
      ]
      if not resultados:
          return {"encontrado": False, "mensaje": "Doctor no encontrado"}
      doctor = resultados[0]
      soup = BeautifulSoup(requests.get(doctor["url"]).text, "html.parser")
      perfil = soup.get_text(separator="\n", strip=True)[:2000]
      return {
          "encontrado": True,
          "nombre": doctor["nombre"],
          "url": doctor["url"],
          "perfil": perfil,
          "otras_coincidencias": [d["nombre"] for d in resultados[1:5]],
      }

  if __name__ == "__main__":
      import uvicorn
      uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
