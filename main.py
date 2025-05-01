import asyncio
from playwright.async_api import async_playwright, TimeoutError
import json

async def run():
    browser = None  # Inicializa browser para el bloque finally

    # Inicia Playwright
    async with async_playwright() as p:
        try:
            # Lanzar navegador (usar Chromium por estabilidad en Replit)
            browser = await p.chromium.launch(
                headless=True,
                # slow_mo=1000,  # Descomenta si quieres ralentizar cada paso
            )

            # Crear contexto con user-agent y tamaño de ventana
            context = await browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/122.0.0.0 Safari/537.36'
                ),
                viewport={'width': 1920, 'height': 1080}
            )

            # Abrir nueva página
            page = await context.new_page()

            # Definir dominios a bloquear
            excluded_domains = [
                'snack-media.com',
                'primis.tech',
                'sekindo.com',
                'cloudfront.net',
                'adsafeprotected.com',
                'doubleclick.net'
            ]

            # Función de bloqueo de anuncios
            async def block_ads(route):
                if any(domain in route.request.url for domain in excluded_domains):
                    await route.abort()
                else:
                    await route.continue_()

            # Registrar handler de rutas para bloquear tráfico no deseado
            await page.route("**/*", block_ads)

            # Navegación a la página objetivo
            print("Navegando a la página...")
            await page.goto("https://vaughn.live/browse/espanol", timeout=60000)

            # Espera explícita de carga
            print("Esperando carga de contenido...")
            await page.wait_for_timeout(5000)

            # Extracción de datos
            print("\nTítulo de la página:")
            page_title = await page.title()
            print(page_title)

            streams_data = []
            streams = await page.query_selector_all('.browsePageStreamBox')
            print(f"\nNúmero de elementos .browsePageStreamBox encontrados: {len(streams)}")

            if not streams:
                debug_path = 'debug_no_streams.png'
                await page.screenshot(path=debug_path)
                print(f"Captura de depuración guardada en {debug_path}")

            for stream in streams:
                try:
                    # Saltar anuncios dentro de streams
                    ad_marker = await stream.query_selector('.browsePageStreamBox_inner2')
                    if ad_marker:
                        continue

                    # Extraer cuenta
                    account_el = await stream.query_selector('.browserPageStreamBox_lower_account')
                    account = (await account_el.inner_text()).strip() if account_el else 'N/A'
                    if account == 'N/A':
                        continue

                    # Extraer estado y espectadores
                    status_els = await stream.query_selector_all(
                        '.browserPageStreamBox_lower_status:not(.browserPageStreamBox_lower_spacer)'
                    )
                    status_texts = [await el.inner_text() for el in status_els]
                    status = status_texts[0].strip() if status_texts else 'Sin estado'
                    viewers = status_texts[1].strip() if len(status_texts) > 1 else '0 Watching'

                    # Construir URLs
                    stream_url = f"https://stream-cdn-iad3.vaughnsoft.net/play/live_{account}.flv|Referer=https://vaughn.live"
                    logo_url = f"https://cdn.vaughnsoft.net/profile/2145/{account}.jpg"

                    streams_data.append({
                        "canal": account,
                        "url": stream_url,
                        "logo": logo_url,
                        "estado": status,
                        "espectadores": viewers
                    })
                except Exception:
                    continue

            # Guardar resultado en JSON
            if streams_data:
                with open('canales.json', 'w', encoding='utf-8') as f:
                    json.dump(streams_data, f, indent=2, ensure_ascii=False)
                print(f"\nDatos de {len(streams_data)} canales guardados en canales.json")
            else:
                print("\nNo se extrajeron datos de streams para guardar.")

        except TimeoutError as e:
            print(f"Timeout general en navegación o extracción: {e}")

        except Exception as e:
            # Errores inesperados
            print(f"Error inesperado: {e}")

        finally:
            if browser:
                print("Cerrando el navegador...")
                await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
