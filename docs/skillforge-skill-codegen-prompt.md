# SkillForge — Skill Kod Üretim Master Promptu

Bu prompt Claude Desktop'ta her skill'in kodunu üretmek için kullanılır.
Önce SYSTEM PROMPT'u ayarla, sonra her skill için ilgili oturum prompt'unu kullan.

---

## SYSTEM PROMPT (bir kez ayarla)

```
Sen SkillForge projesinin kıdemli Python geliştiricisisin.
SkillForge, veritabanı gerektirmeyen, standart input/output'a sahip,
gerçek çalışan kod içeren bir AI skill kütüphanesidir.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEMEL SINIFLAR (her skill bunları kullanır)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# skillforge/base.py
from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Any

class SkillInput(BaseModel):
    data: dict[str, Any]
    metadata: dict[str, Any] = {}

class SkillOutput(BaseModel):
    success: bool
    data: dict[str, Any] = {}
    error: str = ""
    metadata: dict[str, Any] = {}

class BaseWorker(ABC):
    skill_id: str
    version: str = "1.0.0"

    @abstractmethod
    def run(self, input: SkillInput) -> SkillOutput:
        pass

    def safe_run(self, input: SkillInput) -> SkillOutput:
        try:
            return self.run(input)
        except Exception as e:
            return SkillOutput(success=False, error=str(e))

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HER SKILL İÇİN ZORUNLU 4 DOSYA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. schema.json   — Input/output tip tanımları
2. worker.py     — BaseWorker implementasyonu
3. SKILL.md      — Agent kullanım kılavuzu
4. test.py       — pytest testleri (min 5 test)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KESİN KURALLAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- DB YASAK: SQLite, Redis, dosyaya yazma yok
- STATELESS: Her run() çağrısı tamamen bağımsız
- TYPE HINT: Tüm parametre ve dönüşler typed
- HATA: Exception fırlatma, SkillOutput(success=False) döndür
- LOG: print() değil, logging modülü kullan
- TEST: Her test gerçek assert içermeli, pass yazma
- BAĞIMLILIK: Sadece belirtilen paketleri import et
- PLACEHOLDER: "..." veya "TODO" kullanma, tam yaz

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOSYA BAŞLIĞI FORMATI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Her dosyanın ilk satırı:
# filepath: skills/<kategori>/<skill-adi>/<dosya.uzantı>
```

---

## KATEGORİ 1 — UI / HTML (5 skill)

### Prompt 1-A: ui.bootstrap-scaffold

```
Skill: ui.bootstrap-scaffold
Klasör: skills/ui/bootstrap-scaffold/

Görev:
Verilen içerik yapısına (başlık, bölümler, butonlar) göre
sıfırdan Bootstrap 5 HTML sayfası üretir.

Input alanları:
- page_title: string — sayfa başlığı
- sections: list[{title, content, type}] — bölümler
  type: "hero" | "cards" | "table" | "form" | "text"
- navbar: bool — navbar eklensin mi
- theme: "light" | "dark" — Bootstrap teması
- extra_classes: string (opsiyonel) — ek CSS sınıfları

Output alanları:
- html: string — tam HTML dosyası içeriği
- sections_count: int
- estimated_size_kb: float

Kurallar:
- Bootstrap CDN üzerinden yükle (5.3.x)
- Inline style kullanma, Bootstrap class'larını kullan
- Responsive olmalı (col-md-*, col-lg-*)
- Türkçe karakter desteği (charset UTF-8)
- HTML tam ve çalışır halde olmalı (<!DOCTYPE> dahil)

Bağımlılık: sadece Python stdlib (string işleme)

4 dosyayı tam olarak yaz.
Test'lerde: hero section testi, dark theme testi,
navbar=False testi, çoklu section testi, boş input hata testi.
```

---

### Prompt 1-B: ui.react-component

```
Skill: ui.react-component
Klasör: skills/ui/react-component/

Görev:
Bileşen adı, props tanımı ve açıklaması verilince
TypeScript + Tailwind CSS React bileşeni üretir.

Input alanları:
- component_name: string — PascalCase bileşen adı
- description: string — ne yapacağı
- props: list[{name, type, required, default?, description}]
- variant: "button" | "card" | "form" | "list" | "modal" | "generic"
- with_storybook: bool — Storybook story da üretilsin mi

Output alanları:
- component_code: string — .tsx dosya içeriği
- story_code: string — .stories.tsx içeriği (with_storybook=True ise)
- prop_count: int
- has_state: bool — useState kullanılıyor mu

Kurallar:
- TypeScript strict mode uyumlu
- Tailwind utility class'ları kullan, inline style yok
- Props interface ayrı export edilmeli
- React.FC<Props> tipi kullanma, düz fonksiyon yaz
- Default export olmalı
- forwardRef gerekiyorsa ekle

Bağımlılık: stdlib (string işleme)

4 dosyayı tam yaz.
Test'lerde: button variant, form variant, required props,
optional props default değer, geçersiz variant hata testi.
```

---

### Prompt 1-C: ui.tailwind-layout

```
Skill: ui.tailwind-layout
Klasör: skills/ui/tailwind-layout/

Görev:
Ham HTML veya layout tanımını alıp Tailwind utility
class'larıyla responsive layout'a dönüştürür.

Input alanları:
- html: string — dönüştürülecek HTML (inline style veya eski CSS ile)
- breakpoints: list["sm"|"md"|"lg"|"xl"] — hangi breakpoint'ler
- remove_inline_styles: bool — inline style'ları temizlesin mi
- add_dark_mode: bool — dark: prefix eklensin mi

Output alanları:
- converted_html: string — Tailwind class'lı HTML
- removed_styles_count: int
- added_classes_count: int
- warnings: list[string] — dönüştürülemeyen durumlar

Kurallar:
- BeautifulSoup ile parse et
- Yaygın CSS → Tailwind eşleştirme tablosu kullan
  (margin, padding, color, display, flex, grid vb.)
- Birebir karşılığı olmayan CSS için warning ekle
- Orijinal yapıyı koru, sadece class'ları güncelle

Bağımlılık: beautifulsoup4, lxml

4 dosyayı tam yaz.
Test'lerde: margin/padding dönüşümü, flex layout,
grid layout, inline style temizleme, dark mode ekleme.
```

---

### Prompt 1-D: ui.dark-mode-patch

```
Skill: ui.dark-mode-patch
Klasör: skills/ui/dark-mode-patch/

Görev:
Mevcut CSS veya Tailwind HTML dosyasına dark mode desteği ekler.

Input alanları:
- source: string — CSS veya HTML içeriği
- source_type: "css" | "tailwind_html" | "css_variables"
- strategy: "class" | "media_query" | "both"
  class → .dark sınıfı ile (Tailwind dark:)
  media_query → @media (prefers-color-scheme: dark)
  both → ikisini birden
- color_mapping: dict (opsiyonel) — özel renk eşleştirme
  örnek: {"#ffffff": "#1a1a1a", "#000000": "#f5f5f5"}

Output alanları:
- patched_source: string — dark mode eklenmiş içerik
- colors_patched: int — değiştirilen renk sayısı
- manual_review_needed: list[string] — elle kontrol gereken yerler

Kurallar:
- CSS değişkenleri varsa :root + .dark/:root[data-theme="dark"] kullan
- Renk otomatik tersine çevirme: hsl lightness'ı yansıt
- Görsel elementler (border, shadow) için de dark varyant ekle

Bağımlılık: stdlib + re + cssutils (opsiyonel)

4 dosyayı tam yaz.
Test'lerde: CSS media query, Tailwind dark: prefix,
CSS variables, özel renk mapping, karma içerik.
```

---

### Prompt 1-E: ui.figma-to-html

```
Skill: ui.figma-to-html
Klasör: skills/ui/figma-to-html/

Görev:
Figma export JSON yapısından (simplified node tree)
çalışan HTML/CSS üretir.

Input alanları:
- figma_json: dict — Figma node tree (type, name, style, children)
- output_format: "plain_html" | "tailwind" | "bootstrap"
- include_fonts: bool — Google Fonts linki eklensin mi
- responsive: bool — responsive breakpoint'ler eklensin mi

Output alanları:
- html: string — üretilen HTML
- css: string — üretilen CSS (tailwind değilse)
- node_count: int — işlenen node sayısı
- unsupported_nodes: list[string] — desteklenmeyen node tipleri

Figma node tipleri: FRAME, GROUP, TEXT, RECTANGLE,
ELLIPSE, VECTOR, COMPONENT, INSTANCE

Kurallar:
- Recursive node traverse yap
- TEXT node → <p>/<h1-h6>/<span> (font size'a göre)
- RECTANGLE → <div> veya <img> (fills varsa)
- ELLIPSE → border-radius: 50%
- Auto Layout → flexbox
- Desteklenmeyen node'ları atla, warning ekle

Bağımlılık: stdlib

4 dosyayı tam yaz.
Test'lerde: TEXT node, RECTANGLE, nested FRAME,
AUTO_LAYOUT, desteklenmeyen node tipi.
```

---

## KATEGORİ 2 — CSS (3 skill)

### Prompt 2-A: css.minify

```
Skill: css.minify
Klasör: skills/css/minify/

Görev:
CSS dosyasını minify eder, dead code kaldırır,
gzip boyutunu hesaplar ve rapor verir.

Input alanları:
- css: string — ham CSS içeriği
- remove_comments: bool (default: True)
- remove_unused_vars: bool (default: False)
- html_context: string (opsiyonel) — dead code analizi için HTML

Output alanları:
- minified: string — sıkıştırılmış CSS
- original_size_bytes: int
- minified_size_bytes: int
- gzip_size_bytes: int
- reduction_percent: float
- removed_rules_count: int
- warnings: list[string]

Kurallar:
- Yorum satırlarını kaldır (/*! önemli yorumlar hariç)
- Gereksiz boşluk, newline, tab temizle
- Shorthand birleştirme (margin: 0 0 0 0 → margin: 0)
- Renk kısaltma (#ffffff → #fff)
- html_context varsa kullanılmayan selector'ları tespit et
- gzip boyutu: zlib ile hesapla (stdlib)

Bağımlılık: stdlib (re, zlib)

4 dosyayı tam yaz.
Test'lerde: yorum temizleme, boşluk sıkıştırma,
renk kısaltma, boyut hesaplama, boş CSS.
```

---

### Prompt 2-B: css.var-extract

```
Skill: css.var-extract
Klasör: skills/css/var-extract/

Görev:
CSS'teki tekrar eden değerleri (renk, boyut, font)
CSS custom property'e (--var-name) dönüştürür.

Input alanları:
- css: string — orijinal CSS
- min_occurrences: int (default: 2) — kaç tekrarda değişken yapılsın
- prefix: string (default: "--sf") — değişken öneki
- categories: list["color"|"size"|"font"|"shadow"|"radius"]

Output alanları:
- converted_css: string — değişkenli CSS
- variables_css: string — :root { } bloğu
- full_css: string — variables_css + converted_css
- extracted_count: int
- variable_map: dict — {orijinal_değer: değişken_adı}

Kurallar:
- Renk: hex, rgb(), hsl(), named colors tespit et
- Boyut: px, rem, em, % değerleri
- Font: font-family değerleri
- Değişken adı otomatik üret (--sf-color-1, --sf-blue vb.)
- Renklerde anlamlı isim: #ff0000 → --sf-red

Bağımlılık: stdlib (re, collections)

4 dosyayı tam yaz.
Test'lerde: renk çıkarma, boyut çıkarma, min_occurrences=3,
custom prefix, boş CSS.
```

---

### Prompt 2-C: css.bem-converter

```
Skill: css.bem-converter
Klasör: skills/css/bem-converter/

Görev:
Geleneksel CSS sınıflarını BEM naming convention'a dönüştürür.

Input alanları:
- css: string — orijinal CSS
- html: string (opsiyonel) — eşleşen HTML da dönüştürülsün
- block_prefix: string (opsiyonel) — varsayılan blok öneki
- dry_run: bool — değişiklik yapma, sadece önerileri listele

Output alanları:
- converted_css: string
- converted_html: string (html verilmişse)
- rename_map: dict — {eski_sınıf: yeni_bem_sınıf}
- suggestions_count: int
- manual_review: list[string] — BEM'e otomatik çevrilemeyen

BEM formatı: block__element--modifier

Kurallar:
- İç içe selector → element çıkar (.card .title → .card__title)
- :hover, :focus → modifier çıkar (.btn:hover → .btn--hover)
- Kısaltmaları genişlet (btn→button, img→image, nav→navigation)
- Çakışan isimler için uyarı ekle

Bağımlılık: stdlib (re)

4 dosyayı tam yaz.
Test'lerde: nested selector, hover state, HTML dönüşümü,
dry_run modu, karmaşık seçici.
```

---

## KATEGORİ 3 — JavaScript / TypeScript (5 skill)

### Prompt 3-A: js.bundle-analyze

```
Skill: js.bundle-analyze
Klasör: skills/js/bundle-analyze/

Görev:
package.json ve opsiyonel import listesinden
ağır/duplicate bağımlılıkları tespit eder, öneriler sunar.

Input alanları:
- package_json: dict — package.json içeriği (parsed)
- import_list: list[string] (opsiyonel) — kullanılan import'lar
- size_threshold_kb: int (default: 50) — uyarı eşiği

Output alanları:
- heavy_packages: list[{name, approx_size_kb, alternatives}]
- duplicate_packages: list[{name, versions}]
- unused_packages: list[string] (import_list verilmişse)
- total_approx_size_kb: float
- recommendations: list[string]
- score: int — 0-100 arası optimizasyon skoru

Bilinen ağır paketler veritabanı (hardcode dict):
moment(67kb→dayjs 2kb), lodash(71kb→lodash-es/radash),
axios(13kb→ky 3kb), jquery(87kb), bootstrap(48kb),
material-ui(300kb+), antd(500kb+) vb.

Kurallar:
- package.json parse et (dependencies + devDependencies)
- Semver karşılaştırması yap (^, ~, * çözümle)
- Alternatif öneri için bilinen paket listesi kullan
- Score: ağır paket -10, duplicate -5, kullanılmayan -3

Bağımlılık: stdlib

4 dosyayı tam yaz.
Test'lerde: moment tespiti, duplicate versiyon,
kullanılmayan paket, temiz package.json (score:100), boş deps.
```

---

### Prompt 3-B: js.ts-migrate

```
Skill: js.ts-migrate
Klasör: skills/js/ts-migrate/

Görev:
.js dosyasını type inference ile .ts'e çevirir.

Input alanları:
- js_code: string — dönüştürülecek JS kodu
- strict: bool (default: True) — strict mode
- infer_return_types: bool (default: True)
- target: "es2020" | "es2022" | "esnext" (default: "es2022")
- framework: "none" | "react" | "node" (default: "none")

Output alanları:
- ts_code: string — TypeScript kodu
- added_types_count: int
- any_count: int — kaçıncı yerde any kullanıldı
- warnings: list[string] — tip çıkarılamayan yerler
- tsconfig_snippet: dict — önerilen tsconfig ayarları

Dönüşüm kuralları:
- var → let/const (const tercih)
- function params: tip çıkar (default değerden, JSDoc'tan)
- Object literal → interface üret
- Array → typed array (string[], number[] vb.)
- Callback → arrow function tipi
- require() → import
- module.exports → export default / named export
- JSDoc @param/@return varsa kullan, sonra kaldır

Bağımlılık: stdlib (re, ast benzeri regex işleme)

4 dosyayı tam yaz.
Test'lerde: var→const, function tipi, object→interface,
require→import, JSDoc dönüşümü.
```

---

### Prompt 3-C: js.eslint-autofix

```
Skill: js.eslint-autofix
Klasör: skills/js/eslint-autofix/

Görev:
Kod tabanını analiz edip özel .eslintrc.json kuralları önerir
ve mevcut .eslintrc'ye merge eder.

Input alanları:
- code_samples: list[string] — analiz edilecek JS/TS kod örnekleri
- framework: "react" | "vue" | "node" | "generic"
- typescript: bool
- existing_eslintrc: dict (opsiyonel) — mevcut config
- strictness: "relaxed" | "standard" | "strict"

Output alanları:
- eslintrc: dict — önerilen tam .eslintrc.json
- merged_eslintrc: dict (existing verilmişse merge edilmiş)
- rules_added: int
- rules_changed: int
- explanation: dict — {kural_adı: neden_eklendi}

Kural kategorileri:
- Best practices (no-console, no-debugger, eqeqeq)
- Style (indent, quotes, semi)
- React (react-hooks/rules-of-hooks, react/prop-types)
- TypeScript (@typescript-eslint/no-explicit-any)
- Security (no-eval, no-implied-eval)

Bağımlılık: stdlib (json)

4 dosyayı tam yaz.
Test'lerde: React config, Node config, TypeScript strict,
mevcut config merge, relaxed mod.
```

---

### Prompt 3-D: js.env-validator

```
Skill: js.env-validator
Klasör: skills/js/env-validator/

Görev:
.env dosyasını veya env dict'i kontrol eder,
eksik/hatalı/güvensiz değerleri listeler.

Input alanları:
- env_content: string — .env dosyası içeriği (KEY=VALUE formatı)
- schema: dict (opsiyonel) — beklenen değişkenler ve kurallar
  format: {KEY: {required, type, pattern, min_length, secret}}
- check_secrets: bool — API key formatlarını kontrol et

Output alanları:
- valid: bool
- missing_required: list[string]
- type_errors: list[{key, expected, got}]
- weak_secrets: list[{key, reason}]
- exposed_defaults: list[string] — "changeme", "test123" gibi
- parsed: dict — parse edilmiş değerler

Kontroller:
- URL formatı (DATABASE_URL, REDIS_URL)
- Port numarası (1-65535)
- Boolean (true/false/1/0)
- API key pattern (sk-, pk-, Bearer )
- Zayıf değer: "test", "secret", "password", "123456"
- Büyük/küçük harf tutarlılığı

Bağımlılık: stdlib (re)

4 dosyayı tam yaz.
Test'lerde: eksik required, yanlış URL formatı,
zayıf secret, boolean tip, geçerli .env.
```

---

### Prompt 3-E: js.dead-code

```
Skill: js.dead-code
Klasör: skills/js/dead-code/

Görev:
JavaScript/TypeScript dosyasında kullanılmayan
fonksiyon, değişken ve import'ları tespit eder.

Input alanları:
- code: string — JS/TS kodu
- language: "javascript" | "typescript"
- check_exports: bool — export edilip kullanılmayanları da say
- ignore_patterns: list[string] — görmezden gelinecek isim kalıpları

Output alanları:
- unused_functions: list[{name, line, reason}]
- unused_variables: list[{name, line, reason}]
- unused_imports: list[{name, source, line}]
- total_dead_lines: int — tahmini ölü kod satırı
- clean_code: string — ölü kod temizlenmiş versiyon
- confidence: float — 0-1 arası tespit güven skoru

Kurallar:
- Regex tabanlı AST-benzeri analiz
- Tanımla ve kullanım sayısını karşılaştır
- Export edilen fonksiyonlar varsayılan olarak "kullanılıyor"
- _ ile başlayan değişkenler atla (intentionally unused)
- Confidence: basit regex=0.7, çoklu kontrol=0.85

Bağımlılık: stdlib (re, collections)

4 dosyayı tam yaz.
Test'lerde: kullanılmayan fonksiyon, kullanılmayan import,
export edilmiş fonksiyon (atla), _ prefix (atla), temiz kod.
```

---

## KATEGORİ 4 — API (5 skill)

### Prompt 4-A: api.rest-scaffold

```
Skill: api.rest-scaffold
Klasör: skills/api/rest-scaffold/

Görev:
OpenAPI 3.0 şemasından FastAPI veya Express.js
route kodu üretir.

Input alanları:
- openapi_schema: dict — OpenAPI 3.0 schema (parsed JSON)
- framework: "fastapi" | "express"
- include_auth: bool — JWT auth middleware eklensin mi
- include_validation: bool — request validation eklensin mi
- output_structure: "single_file" | "router_per_tag"

Output alanları:
- files: dict[str, str] — {dosya_yolu: içerik}
- endpoint_count: int
- model_count: int — üretilen Pydantic/Joi model sayısı
- warnings: list[string]

FastAPI kuralları:
- Her endpoint için Pydantic request/response model
- Tip annotasyonlar tam
- HTTPException kullan
- Router'ları tag'e göre ayır

Express kuralları:
- express-validator ile validation
- try/catch + next(err) pattern
- Router.js ayrı dosya

Bağımlılık: stdlib

4 dosyayı tam yaz.
Test'lerde: GET endpoint, POST+validation, auth endpoint,
birden fazla tag, boş schema hata.
```

---

### Prompt 4-B: api.mock-server

```
Skill: api.mock-server
Klasör: skills/api/mock-server/

Görev:
OpenAPI şeması veya JSON örnek verisinden
statik mock response dosyaları üretir.

Input alanları:
- schema: dict — OpenAPI schema veya örnek response dict
- input_type: "openapi" | "example_json"
- framework: "json_server" | "msw" | "raw_json"
- include_errors: bool — hata response'ları da üret (400,404,500)
- realistic_data: bool — faker benzeri gerçekçi veriler

Output alanları:
- mock_files: dict[str, str] — {endpoint_path: json_içerik}
- handler_code: string (msw ise) — handlers.js içeriği
- db_json: string (json_server ise) — db.json içeriği
- endpoint_count: int

Gerçekçi veri üretimi (faker'sız, hardcode listeler):
- İsim: Türkçe isim listesi (50 isim)
- Email: isim@domain.com formatı
- Telefon: +90 5XX XXX XXXX
- Tarih: ISO 8601, son 1 yıl içinde random
- UUID: uuid.uuid4()
- Metin: Türkçe lorem ipsum paragrafları

Bağımlılık: stdlib (uuid, random, datetime)

4 dosyayı tam yaz.
Test'lerde: OpenAPI GET, POST mock, hata response,
MSW handler, gerçekçi veri formatı.
```

---

### Prompt 4-C: api.postman-export

```
Skill: api.postman-export
Klasör: skills/api/postman-export/

Görev:
OpenAPI şeması veya endpoint listesinden
Postman Collection v2.1 formatı üretir.

Input alanları:
- source: dict — OpenAPI schema veya endpoint listesi
- source_type: "openapi" | "endpoint_list"
- collection_name: string
- base_url: string — örn: https://api.example.com
- include_tests: bool — Postman test script'leri eklensin mi
- include_auth: bool — Bearer token auth eklensin mi
- environment_name: string (opsiyonel)

Output alanları:
- collection_json: string — Postman Collection v2.1 JSON
- environment_json: string (opsiyonel) — Postman Environment JSON
- request_count: int
- folder_count: int

Postman Collection v2.1 yapısı:
{info, item: [folder > request], variable, auth}

Test script'leri (include_tests=True):
- Status code kontrolü (200, 201)
- Response time < 2000ms
- Content-Type header kontrolü
- Response body JSON parse edilebilir mi

Bağımlılık: stdlib (json, uuid)

4 dosyayı tam yaz.
Test'lerde: OpenAPI dönüşümü, test script ekleme,
auth ekleme, folder yapısı, environment üretme.
```

---

### Prompt 4-D: api.rate-limit-check

```
Skill: api.rate-limit-check
Klasör: skills/api/rate-limit-check/

Görev:
API endpoint'ini belirli istek sayısıyla test eder,
rate limit davranışını tespit eder.

Input alanları:
- url: string — test edilecek endpoint
- method: "GET" | "POST" | "PUT" | "DELETE"
- headers: dict — request header'ları
- body: dict (opsiyonel) — POST/PUT body
- request_count: int (default: 20)
- interval_ms: int (default: 100) — istekler arası bekleme
- timeout_seconds: int (default: 10)

Output alanları:
- total_requests: int
- successful: int — 2xx count
- rate_limited: int — 429 count
- errors: int — diğer hatalar
- rate_limit_detected: bool
- limit_headers: dict — X-RateLimit-*, Retry-After
- avg_response_ms: float
- timeline: list[{request_n, status_code, response_ms}]

Kurallar:
- httpx.AsyncClient ile async istek
- 429 aldığında Retry-After header'ı oku
- Her isteğin response süresini kaydet
- Max 100 istek (güvenlik limiti)
- HTTPS sertifika hatalarını raporla, ignore etme

Bağımlılık: httpx, asyncio

4 dosyayı tam yaz.
Test'lerde: başarılı istekler, 429 simülasyonu (mock),
timeout, geçersiz URL, header tespiti.
```

---

### Prompt 4-E: api.webhook-validator

```
Skill: api.webhook-validator
Klasör: skills/api/webhook-validator/

Görev:
Gelen webhook payload'ını JSON şemasına göre doğrular,
HMAC imzasını kontrol eder.

Input alanları:
- payload: dict — webhook payload
- schema: dict — JSON Schema (draft-7)
- signature: string (opsiyonel) — X-Hub-Signature-256 benzeri
- secret: string (opsiyonel) — HMAC secret
- signature_algorithm: "sha256" | "sha1" (default: "sha256")
- provider: "github" | "stripe" | "generic" (default: "generic")

Output alanları:
- valid: bool
- schema_errors: list[{path, message, value}]
- signature_valid: bool | None (imza yoksa None)
- provider_specific: dict — provider'a özel kontroller
- warnings: list[string]

Provider özel kontroller:
- GitHub: X-GitHub-Event header, action field
- Stripe: type field, livemode bool, api_version

Kurallar:
- jsonschema ile validate et
- HMAC: hmac.new(secret, payload_bytes, hashlib.sha256)
- Signature format: "sha256=<hex>" (GitHub tarzı)
- Payload bytes: json.dumps(payload, sort_keys=True).encode()

Bağımlılık: jsonschema, stdlib (hmac, hashlib)

4 dosyayı tam yaz.
Test'lerde: geçerli payload, schema hatası, geçerli HMAC,
geçersiz HMAC, GitHub provider.
```

---

## KATEGORİ 5 — VERİ (6 skill)

### Prompt 5-A: data.json-to-csv

```
Skill: data.json-to-csv
Klasör: skills/data/json-to-csv/

Görev:
Nested JSON array'i düzleştirip UTF-8 CSV'ye çevirir.

Input alanları:
- json_data: list[dict] | string — JSON verisi
- flatten_nested: bool (default: True) — nested objeleri düzleştir
- separator: string (default: ".") — nested key separator
- columns: list[string] (opsiyonel) — dahil edilecek kolonlar
- encoding: "utf-8" | "utf-8-bom" — BOM: Excel uyumu
- delimiter: "," | ";" | "\t" (default: ",")
- include_index: bool (default: False)

Output alanları:
- csv_content: string — CSV içeriği
- row_count: int
- column_count: int
- columns_list: list[string]
- skipped_columns: list[string]

Düzleştirme: {"user": {"name": "Ali"}} → user.name: "Ali"
Liste değerleri: [1,2,3] → "1;2;3" (join ile)

Bağımlılık: stdlib (csv, json)

4 dosyayı tam yaz.
Test'lerde: düz JSON, nested JSON, BOM encoding,
custom delimiter, columns filtresi.
```

---

### Prompt 5-B: data.csv-clean

```
Skill: data.csv-clean
Klasör: skills/data/csv-clean/

Görev:
CSV dosyasını temizler: boş satır, duplicate,
tip hataları kaldırır, rapor verir.

Input alanları:
- csv_content: string — ham CSV
- delimiter: string (default: ",")
- operations: list["remove_empty"|"remove_duplicates"|
  "fix_encoding"|"trim_whitespace"|"normalize_dates"|
  "remove_nulls"|"fix_types"]
- date_columns: list[string] — tarih kolonları (normalize için)
- date_format: string (default: "%Y-%m-%d")
- duplicate_subset: list[string] (opsiyonel) — hangi kolonlara göre

Output alanları:
- cleaned_csv: string
- original_rows: int
- cleaned_rows: int
- removed_rows: int
- operations_log: list[{operation, affected_rows, details}]
- column_types: dict — {kolon: tespit_edilen_tip}

Bağımlılık: stdlib (csv, re, datetime)

4 dosyayı tam yaz.
Test'lerde: boş satır temizleme, duplicate kaldırma,
whitespace trim, tarih normalize, karma operasyon.
```

---

### Prompt 5-C: data.pdf-extract

```
Skill: data.pdf-extract
Klasör: skills/data/pdf-extract/

Görev:
PDF'den metin ve tabloları çıkarır.

Input alanları:
- pdf_source: string — dosya yolu veya base64 encoded PDF
- source_type: "filepath" | "base64"
- pages: list[int] (opsiyonel) — hangi sayfalar, None=tümü
- extract_tables: bool (default: True)
- extract_images_meta: bool (default: False) — görsel metadata

Output alanları:
- text: string — tüm metin
- pages: list[{page_number, text, word_count}]
- tables: list[{page, table_index, headers, rows, row_count}]
- total_pages: int
- total_words: int
- has_images: bool
- metadata: dict — title, author, creation_date

Kurallar:
- pdfplumber kullan (pdfminer üstü)
- Tablo: lattice mode önce, sonra stream mode
- Sayfa boşsa text: "" ile ekle, atma
- base64: tempfile ile decode et, işle, sil
- Büyük PDF (>50 sayfa): sayfa sayısını logla

Bağımlılık: pdfplumber, stdlib (base64, tempfile)

4 dosyayı tam yaz.
Test'lerde: metin çıkarma, tablo çıkarma, belirli sayfa,
base64 input, boş sayfa yönetimi.
```

---

### Prompt 5-D: data.excel-to-json

```
Skill: data.excel-to-json
Klasör: skills/data/excel-to-json/

Görev:
xlsx/xls dosyasını sheet bazlı JSON'a çevirir.

Input alanları:
- file_source: string — dosya yolu veya base64
- source_type: "filepath" | "base64"
- sheets: list[string] (opsiyonel) — hangi sheet'ler, None=tümü
- header_row: int (default: 0) — header satır indexi
- skip_empty_rows: bool (default: True)
- date_format: string (default: "iso") — "iso" | "timestamp" | "string"
- include_formulas: bool (default: False)

Output alanları:
- sheets: dict[str, list[dict]] — {sheet_adı: [satırlar]}
- sheet_names: list[string]
- total_rows: int — tüm sheet'lerdeki toplam satır
- column_types: dict[str, dict] — {sheet: {kolon: tip}}
- warnings: list[string]

Kurallar:
- openpyxl kullan (xlsx için)
- xlrd kullan (xls için, sadece okuma)
- Tarih: datetime → ISO string
- None değerler: null olarak tut
- Merged cell: her hücreye değeri kopyala

Bağımlılık: openpyxl, stdlib

4 dosyayı tam yaz.
Test'lerde: tek sheet, çoklu sheet, tarih kolonları,
boş satır atlama, base64 input.
```

---

### Prompt 5-E: data.shapefile-convert

```
Skill: data.shapefile-convert
Klasör: skills/data/shapefile-convert/

Görev:
Shapefile → GeoJSON / KML / KMZ dönüşümü,
CRS dönüşümü dahil.

Input alanları:
- shapefile_path: string — .shp dosyası yolu
  (aynı klasörde .dbf, .shx olmalı)
- output_format: "geojson" | "kml" | "kmz"
- target_crs: string (default: "EPSG:4326")
- simplify_tolerance: float (opsiyonel) — polygon basitleştirme
- properties_filter: list[string] (opsiyonel) — dahil edilecek alanlar

Output alanları:
- converted: string — GeoJSON/KML içeriği
- output_path: string (kmz ise) — oluşturulan dosya yolu
- feature_count: int
- source_crs: string
- geometry_types: list[string] — Point, Polygon vb.
- bounds: dict — {minx, miny, maxx, maxy}

Kurallar:
- geopandas + pyproj kullan
- KML: simplekml ile üret
- KMZ: KML'i zip ile sıkıştır (.kmz = zip içinde .kml)
- CRS dönüşümü: .to_crs(target_crs)
- Simplify: .simplify(tolerance, preserve_topology=True)

Bağımlılık: geopandas, pyproj, simplekml, stdlib (zipfile)

4 dosyayı tam yaz.
Test'lerde: GeoJSON çıktı, KML çıktı, KMZ çıktı,
CRS dönüşümü, properties filtresi.
```

---

### Prompt 5-F: data.schema-infer

```
Skill: data.schema-infer
Klasör: skills/data/schema-infer/

Görev:
Örnek JSON verisinden otomatik JSON Schema (draft-7) üretir.

Input alanları:
- sample_data: list[dict] | dict — örnek JSON
- title: string (opsiyonel) — schema başlığı
- required_threshold: float (default: 1.0)
  — kaç örneğin % kaçında varsa required say
- additional_properties: bool (default: False)
- detect_formats: bool (default: True)
  — email, date, uri, uuid formatları tespit et

Output alanları:
- schema: dict — JSON Schema draft-7
- schema_json: string — formatlanmış JSON string
- field_count: int
- required_count: int
- detected_formats: dict — {alan: format}

Tip tespiti:
- str: email regex, ISO date, URI, UUID → format ekle
- int/float: minimum/maximum örneklerden çıkar
- list: items tipi çıkar
- dict: recursive schema üret
- None olan alanlar: ["type", null] ekle

Bağımlılık: stdlib (json, re)

4 dosyayı tam yaz.
Test'lerde: basit obje, nested obje, array items,
format tespiti (email), required_threshold=0.5.
```

---

## KATEGORİ 6 — MEDYA (7 skill)

### Prompt 6-A: img.compress

```
Skill: img.compress
Klasör: skills/media/img-compress/

Görev:
JPEG/PNG/WebP görselini sıkıştırır,
kalite/boyut dengesi raporu verir.

Input alanları:
- image_source: string — dosya yolu veya base64
- source_type: "filepath" | "base64"
- format: "jpeg" | "png" | "webp" | "auto" — auto: orijinali koru
- quality: int (default: 85) — 1-100
- max_width: int (opsiyonel) — bu genişliği aşarsa küçült
- max_height: int (opsiyonel)
- strip_metadata: bool (default: True)

Output alanları:
- compressed_base64: string — sıkıştırılmış görsel
- original_size_bytes: int
- compressed_size_bytes: int
- reduction_percent: float
- final_width: int
- final_height: int
- format_used: string

Kurallar:
- Pillow kullan
- PNG: optimize=True, compress_level=9
- JPEG: optimize=True, progressive=True
- WebP: method=6 (en iyi sıkıştırma)
- EXIF strip: ImageOps.exif_transpose sonra info temizle
- BytesIO kullan, disk yazma

Bağımlılık: Pillow, stdlib (base64, io)

4 dosyayı tam yaz.
Test'lerde: JPEG sıkıştırma, PNG sıkıştırma,
max_width küçültme, metadata strip, base64 input.
```

---

### Prompt 6-B: img.resize-batch

```
Skill: img.resize-batch
Klasör: skills/media/img-resize-batch/

Görev:
Klasördeki tüm görselleri hedef boyuta getirir,
oranı korur.

Input alanları:
- input_paths: list[string] — görsel dosya yolları
- width: int (opsiyonel)
- height: int (opsiyonel)
- fit_mode: "contain" | "cover" | "fill" | "width_only" | "height_only"
- output_dir: string — çıktı klasörü
- output_format: string (opsiyonel) — None: orijinali koru
- quality: int (default: 90)
- overwrite: bool (default: False)

Output alanları:
- processed: list[{input, output, original_size, new_size, status}]
- success_count: int
- error_count: int
- total_size_before_bytes: int
- total_size_after_bytes: int

Fit mode:
- contain: oranı koruyarak sığdır, boşluk bırak
- cover: oranı koruyarak kapla, kırp
- fill: oranı boz, tam doldur
- width_only / height_only: tek boyut, diğeri orantılı

Bağımlılık: Pillow, stdlib (os, pathlib)

4 dosyayı tam yaz.
Test'lerde: contain modu, cover modu, width_only,
format dönüşümü, overwrite=False (atlama).
```

---

### Prompt 6-C: img.to-webp

```
Skill: img.to-webp
Klasör: skills/media/img-to-webp/

Görev:
PNG/JPEG/GIF görsellerini WebP'ye çevirir,
alfa kanalını korur.

Input alanları:
- images: list[{source: str, source_type: "filepath"|"base64"}]
- quality: int (default: 80) — kayıplı sıkıştırma
- lossless: bool (default: False) — PNG için önerilir
- method: int (default: 4) — 0-6, 6=en iyi/yavaş
- preserve_alpha: bool (default: True)
- exact: bool (default: False) — lossless exact mode

Output alanları:
- results: list[{
    original_format, original_size_bytes,
    webp_base64, webp_size_bytes,
    reduction_percent, has_alpha
  }>]
- total_original_bytes: int
- total_webp_bytes: int
- avg_reduction_percent: float

Kurallar:
- Pillow WebP encoder kullan
- GIF: ilk frame al (animasyon desteklenmiyor, warning ekle)
- RGBA PNG: preserve_alpha=True ile alfa koru
- RGB JPEG: alfa yok, lossless anlamsız → warning

Bağımlılık: Pillow, stdlib (base64, io)

4 dosyayı tam yaz.
Test'lerde: JPEG→WebP, PNG+alpha→WebP, lossless mod,
GIF uyarısı, batch işlem.
```

---

### Prompt 6-D: img.placeholder-gen

```
Skill: img.placeholder-gen
Klasör: skills/media/img-placeholder/

Görev:
Boyut, renk ve metin verilince SVG veya PNG
placeholder görsel üretir.

Input alanları:
- width: int
- height: int
- format: "svg" | "png" | "base64_png"
- bg_color: string (default: "#cccccc") — hex renk
- text_color: string (default: "#666666")
- text: string (opsiyonel) — None: "WxH" otomatik yazar
- font_size: int (opsiyonel) — None: boyuta göre otomatik
- border: bool (default: False)
- border_color: string (default: "#999999")

Output alanları:
- content: string — SVG string veya base64 PNG
- width: int
- height: int
- format: string
- size_bytes: int

SVG kuralları:
- viewBox ve width/height attribute
- <rect> arka plan
- <text> ortada, dominant-baseline: middle, text-anchor: middle
- Font: system-ui, sans-serif
- Border: <rect> stroke ile

PNG kuralları:
- Pillow ImageDraw ile çiz
- Font: load_default() (harici font gerektirme)

Bağımlılık: Pillow (PNG için), stdlib (SVG için yok)

4 dosyayı tam yaz.
Test'lerde: SVG çıktı, PNG çıktı, custom metin,
otomatik metin (WxH), base64 PNG.
```

---

### Prompt 6-E: img.meta-strip

```
Skill: img.meta-strip
Klasör: skills/media/img-meta-strip/

Görev:
Görseldeki EXIF/IPTC/XMP metadata'yı temizler,
KVKK/GDPR uyumu için kullanılır.

Input alanları:
- image_source: string — dosya yolu veya base64
- source_type: "filepath" | "base64"
- strip_mode: "all" | "selective"
- keep_fields: list[string] (selective modda) — korunacak alanlar
  örn: ["ColorSpace", "Orientation"]
- report_before: bool (default: True) — temizleme öncesi rapor

Output alanları:
- clean_image_base64: string
- stripped_fields: list[{tag, name, value_preview}]
- kept_fields: list[{tag, name, value}]
- had_gps: bool — GPS verisi vardı mı
- had_personal: bool — kişisel veri içeriyordu mu
  (Author, Artist, Copyright, CameraOwnerName)
- size_before_bytes: int
- size_after_bytes: int

Kurallar:
- Pillow ile EXIF oku: image._getexif() veya piexif
- "all" mod: yeni Image oluştur, metadata'sız kaydet
- "selective": sadece belirtilenleri koru
- GPS tags: 0x8825 (GPSInfo)
- Kişisel tags: 0x013B, 0xA500, 0x8298 vb.

Bağımlılık: Pillow, piexif, stdlib (base64, io)

4 dosyayı tam yaz.
Test'lerde: tüm meta temizleme, GPS tespiti,
selective mod, kişisel veri tespiti, meta'sız görsel.
```

---

### Prompt 6-F: media.video-thumbnail

```
Skill: media.video-thumbnail
Klasör: skills/media/video-thumbnail/

Görev:
Video dosyasından belirli saniyede kare çıkarır.

Input alanları:
- video_path: string — video dosyası yolu
- timestamps: list[float] — saniye cinsinden zaman damgaları
- output_format: "jpeg" | "png" | "webp" (default: "jpeg")
- width: int (opsiyonel) — thumbnail genişliği
- height: int (opsiyonel)
- quality: int (default: 85)

Output alanları:
- thumbnails: list[{
    timestamp, base64, width, height,
    format, size_bytes
  }>]
- video_duration_seconds: float
- video_width: int
- video_height: int
- fps: float

Kurallar:
- ffmpeg-python veya subprocess+ffmpeg kullan
- ffmpeg yüklü değilse anlamlı hata ver
- timestamp video süresini aşıyorsa skip + warning
- Çoklu timestamp: paralel değil, sıralı işle (güvenli)
- Çıktı: BytesIO → base64

Bağımlılık: ffmpeg-python veya subprocess (ffmpeg binary)

4 dosyayı tam yaz.
Test'lerde: geçerli timestamp, süresi aşan timestamp,
çoklu frame, format seçimi, ffmpeg yoksa hata.
```

---

### Prompt 6-G: media.audio-trim

```
Skill: media.audio-trim
Klasör: skills/media/audio-trim/

Görev:
Ses dosyasını başlangıç-bitiş ms ile keser.

Input alanları:
- audio_source: string — dosya yolu veya base64
- source_type: "filepath" | "base64"
- audio_format: string — "mp3" | "wav" | "ogg" | "m4a"
- start_ms: int — kesim başlangıcı (milisaniye)
- end_ms: int (opsiyonel) — None: dosya sonuna kadar
- output_format: string (default: orijinalle aynı)
- fade_in_ms: int (default: 0) — fade in süresi
- fade_out_ms: int (default: 0) — fade out süresi
- normalize: bool (default: False) — ses seviyesi normalize

Output alanları:
- trimmed_base64: string
- original_duration_ms: int
- trimmed_duration_ms: int
- output_format: string
- size_bytes: int

Kurallar:
- pydub kullan
- AudioSegment[start:end] ile kes
- fade_in: audio.fade_in(ms)
- normalize: effects.normalize(audio)
- BytesIO çıktı, disk yazma

Bağımlılık: pydub, stdlib (base64, io)

4 dosyayı tam yaz.
Test'lerde: basit kesim, fade in/out, end_ms=None,
normalize, geçersiz timestamp hata.
```

---

## KATEGORİ 7 — KOD ARAÇLARI (8 skill)

### Prompt 7-A: code.boilerplate

```
Skill: code.boilerplate
Klasör: skills/code/boilerplate/

Görev:
FastAPI, Next.js veya React için klasör yapısı
ve temel dosyaları üretir.

Input alanları:
- framework: "fastapi" | "nextjs" | "react" | "express"
- project_name: string
- features: list["auth"|"database"|"docker"|"testing"|
  "ci_cd"|"i18n"|"api_client"|"state_management"]
- python_version: string (default: "3.11") — FastAPI için
- node_version: string (default: "20") — JS için
- package_manager: "npm" | "yarn" | "pnpm" (default: "npm")

Output alanları:
- files: dict[str, str] — {dosya_yolu: içerik}
- file_count: int
- directory_structure: string — tree formatında
- setup_commands: list[string] — kurulum komutları
- readme_snippet: string — projeye özel README bölümü

FastAPI dosyaları: main.py, requirements.txt,
.env.example, Dockerfile, docker-compose.yml,
app/routers/, app/models/, app/schemas/, app/core/

Next.js dosyaları: package.json, tsconfig.json,
next.config.js, tailwind.config.js, app/layout.tsx,
app/page.tsx, components/, lib/, public/

Bağımlılık: stdlib

4 dosyayı tam yaz.
Test'lerde: FastAPI minimal, FastAPI+docker,
Next.js minimal, React+testing, setup commands doğruluğu.
```

---

### Prompt 7-B: code.readme-gen

```
Skill: code.readme-gen
Klasör: skills/code/readme-gen/

Görev:
Kod tabanı analizi veya proje tanımından
markdown README yazar.

Input alanları:
- project_info: dict — {
    name, description, language, framework,
    features: list, installation_steps: list,
    env_vars: dict, api_endpoints: list,
    license, author, github_url
  }
- style: "minimal" | "standard" | "detailed"
- include_badges: bool (default: True)
- language: "en" | "tr" (default: "en")
- include_contributing: bool (default: False)

Output alanları:
- readme_content: string — tam markdown
- section_count: int
- word_count: int
- has_badges: bool

Bölümler (style'a göre):
- minimal: başlık, açıklama, kurulum, kullanım
- standard: + badges, özellikler, env vars, lisans
- detailed: + contributing, API docs, screenshots placeholder, changelog link

Badge formatı (Shields.io markdown):
![Python](https://img.shields.io/badge/python-3.11-blue)

Bağımlılık: stdlib

4 dosyayı tam yaz.
Test'lerde: minimal style, detailed style, Türkçe,
badge üretimi, env vars tablosu.
```

---

### Prompt 7-C: code.docstring

```
Skill: code.docstring
Klasör: skills/code/docstring/

Görev:
Python fonksiyonlarına Google veya NumPy style
docstring ekler.

Input alanları:
- source_code: string — Python kaynak kodu
- style: "google" | "numpy" | "sphinx"
- overwrite_existing: bool (default: False)
- include_examples: bool (default: True)
- language: "en" | "tr" (default: "en")
- use_ai: bool (default: False) — Ollama ile açıklama üret

Output alanları:
- documented_code: string — docstring'li kod
- functions_documented: int
- functions_skipped: int — already documented
- classes_documented: int

Google style:
def func(x: int, y: str) -> bool:
    """Kısa açıklama.

    Args:
        x: x parametresi açıklaması.
        y: y parametresi açıklaması.

    Returns:
        Dönüş değeri açıklaması.

    Raises:
        ValueError: Hata durumu.
    """

Kurallar:
- ast modülü ile parse et
- Mevcut docstring varsa overwrite_existing'e göre karar ver
- Tip annotasyondan Args bölümü üret
- Return tipi varsa Returns bölümü ekle
- Exception raise ediyorsa Raises bölümü ekle

Bağımlılık: stdlib (ast)

4 dosyayı tam yaz.
Test'lerde: basit fonksiyon, class metodu, existing docstring,
Türkçe, type hints'ten çıkarım.
```

---

### Prompt 7-D: code.test-gen

```
Skill: code.test-gen
Klasör: skills/code/test-gen/

Görev:
Python fonksiyonundan pytest test case'leri üretir.

Input alanları:
- source_code: string — test edilecek Python kodu
- test_style: "unit" | "integration" | "both"
- coverage_target: "happy_path" | "edge_cases" | "full"
  full: happy + edge + error cases
- mock_external: bool (default: True) — httpx, DB vb. mock'la
- use_fixtures: bool (default: True)
- test_file_name: string (default: "test_generated.py")

Output alanları:
- test_code: string — tam pytest dosyası
- test_count: int
- functions_covered: list[string]
- mock_count: int — kaç mock eklendi
- coverage_estimate: float — tahmini coverage %

Test yapısı:
- Her fonksiyon için ayrı test class
- happy path: beklenen çıktı
- edge cases: boş input, sınır değerler, None
- error cases: exception beklenti (pytest.raises)
- fixture: tekrar eden setup'lar

Kurallar:
- ast ile fonksiyon signature'larını çıkar
- Dönüş tipinden assertion üret
- httpx, requests → unittest.mock.patch
- DB işlemleri → pytest-mock ile mock

Bağımlılık: stdlib (ast)

4 dosyayı tam yaz.
Test'lerde: happy path üretimi, edge case, exception test,
mock üretimi, fixture kullanımı.
```

---

### Prompt 7-E: code.changelog

```
Skill: code.changelog
Klasör: skills/code/changelog/

Görev:
Git log çıktısından Conventional Commits
standardında CHANGELOG.md üretir.

Input alanları:
- git_log: string — "git log --oneline --pretty=format:'%H|%s|%an|%ad'" çıktısı
- version: string — yeni versiyon (örn: "1.2.0")
- previous_version: string (opsiyonel)
- repo_url: string (opsiyonel) — commit link için
- date: string (default: bugün) — ISO format
- include_authors: bool (default: False)

Output alanları:
- changelog_md: string — CHANGELOG.md içeriği
- feat_count: int
- fix_count: int
- breaking_count: int
- total_commits: int

Conventional Commits kategorileri:
- feat: → ### Features
- fix: → ### Bug Fixes
- docs: → ### Documentation
- chore: → ### Maintenance
- refactor: → ### Refactoring
- perf: → ### Performance
- test: → ### Tests
- BREAKING CHANGE: → ### ⚠ Breaking Changes (en üste)

Format (Keep a Changelog):
## [1.2.0] - 2025-04-10
### Features
- feat açıklaması ([abc1234](repo_url/commit/abc1234))

Bağımlılık: stdlib (re, datetime)

4 dosyayı tam yaz.
Test'lerde: feat+fix commits, breaking change,
repo_url ile link, boş log, karma commit tipleri.
```

---

### Prompt 7-F: code.pr-summary

```
Skill: code.pr-summary
Klasör: skills/code/pr-summary/

Görev:
Git diff verilince PR başlık ve açıklaması yazar.

Input alanları:
- diff: string — "git diff main...feature" çıktısı
- branch_name: string (opsiyonel)
- ticket_id: string (opsiyonel) — Jira/Linear ticket
- template: "github" | "gitlab" | "minimal"
- language: "en" | "tr" (default: "en")
- use_ai: bool (default: False) — Ollama ile içerik üret

Output alanları:
- title: string — PR başlığı (conventional commit formatında)
- body: string — PR açıklama markdown
- labels: list[string] — önerilen etiketler
- reviewers_hint: list[string] — hangi alanlar değişti
- breaking_changes: list[string]

Template bölümleri:
- github: ## Summary, ## Changes, ## Testing, ## Screenshots
- gitlab: ## What, ## Why, ## How, ## Testing
- minimal: ## Changes, ## Notes

Diff analizi:
- Eklenen/silinen dosya sayısı
- Değiştirilen fonksiyon isimleri (def/function)
- Test dosyası değişti mi
- Config dosyası değişti mi (.env, config, yaml)
- Breaking: API endpoint silindi mi, schema değişti mi

Bağımlılık: stdlib (re)

4 dosyayı tam yaz.
Test'lerde: yeni feature diff, bug fix diff,
config değişikliği, breaking change tespiti, Türkçe.
```

---

### Prompt 7-G: code.regex-builder

```
Skill: code.regex-builder
Klasör: skills/code/regex-builder/

Görev:
Doğal dil açıklamasından regex üretir,
test case'leri dahil.

Input alanları:
- description: string — ne eşleşmeli (Türkçe veya İngilizce)
- examples_match: list[string] — eşleşmeli örnekler
- examples_no_match: list[string] — eşleşmemeli örnekler
- language: "python" | "javascript" | "go"
- flags: list["IGNORECASE"|"MULTILINE"|"DOTALL"]
- named_groups: bool (default: False)

Output alanları:
- pattern: string — regex pattern
- flags_used: list[string]
- explanation: string — pattern açıklaması (parça parça)
- test_results: list[{input, expected, actual, passed}]
- usage_example: string — hedef dilde kullanım örneği
- alternatives: list[string] — alternatif pattern'lar

Yaygın pattern kütüphanesi (hardcode):
- Türkçe telefon, TC kimlik no, IBAN, posta kodu
- Email, URL, IPv4, IPv6
- ISO date, credit card (masked), hex color
- Semantic version, UUID

Kurallar:
- re modülü ile pattern'ı test et
- examples_match hepsini yakalamalı
- examples_no_match hiçbirini yakalamamalı
- Pattern yanlışsa warning ekle, en yakın alternatifi ver

Bağımlılık: stdlib (re)

4 dosyayı tam yaz.
Test'lerde: email regex, Türkçe telefon, tarih pattern,
named groups, match/no-match doğrulama.
```

---

### Prompt 7-H: code.env-template

```
Skill: code.env-template
Klasör: skills/code/env-template/

Görev:
Kaynak koddan .env değişkenlerini tespit eder,
açıklamalı .env.example üretir.

Input alanları:
- source_files: list[{path: str, content: str}]
- existing_env: string (opsiyonel) — mevcut .env içeriği
- add_comments: bool (default: True)
- add_defaults: bool (default: True)
- group_by_service: bool (default: True) — DB, Redis, API vb.
- output_format: "env" | "yaml" | "json"

Output alanları:
- template: string — .env.example içeriği
- variables: list[{
    name, description, required, default,
    service_group, detected_in_files
  }>]
- variable_count: int
- required_count: int

Tespit patternleri:
- os.environ.get("KEY")
- os.getenv("KEY", "default")
- process.env.KEY (JS)
- settings.KEY (Django)
- env("KEY") (Laravel)
- config("KEY") (genel)

Gruplama:
- DATABASE_* → # Database
- REDIS_* → # Cache
- JWT_*, SECRET_* → # Security
- SMTP_*, EMAIL_* → # Email
- S3_*, AWS_* → # Storage

Bağımlılık: stdlib (re)

4 dosyayı tam yaz.
Test'lerde: os.getenv tespiti, default değer çıkarma,
gruplama, mevcut .env ile merge, YAML format.
```

---

## KATEGORİ 8 — AI / LLM (6 skill)

### Prompt 8-A: ai.prompt-engineer

```
Skill: ai.prompt-engineer
Klasör: skills/ai/prompt-engineer/

Görev:
Ham kullanıcı isteğini yapılandırılmış,
etkili LLM prompt'una dönüştürür.

Input alanları:
- raw_request: string — ham istek
- target_model: "gpt-4" | "claude" | "gemma" | "llama" | "generic"
- task_type: "generation" | "extraction" | "classification" |
  "summarization" | "translation" | "code" | "analysis"
- output_format: "text" | "json" | "markdown" | "list"
- language: "tr" | "en" (default: "tr")
- add_examples: bool (default: True) — few-shot örnekler
- chain_of_thought: bool (default: False) — CoT ekle

Output alanları:
- system_prompt: string
- user_prompt: string
- full_prompt: string — ikisini birleştirir
- techniques_used: list[string]
- token_estimate: int — yaklaşık token sayısı
- suggestions: list[string] — daha iyi sonuç için öneriler

Teknikler:
- Role assignment: "Sen bir X uzmansın"
- Context window: görev bağlamı
- Output constraints: format, uzunluk, dil
- Few-shot: 2-3 örnek input/output
- CoT: "Adım adım düşün:"
- Negative prompting: "...yapma"

Bağımlılık: stdlib

4 dosyayı tam yaz.
Test'lerde: kod üretimi, veri çıkarma, JSON format,
CoT ekleme, Türkçe prompt.
```

---

### Prompt 8-B: ai.ollama-orchestrate

```
Skill: ai.ollama-orchestrate
Klasör: skills/ai/ollama-orchestrate/

Görev:
Birden fazla Ollama modelini pipeline olarak çalıştırır,
çıktıları birleştirir.

Input alanları:
- pipeline: list[{
    model: str,
    prompt_template: str,
    role: str,
    output_key: str
  }>] — sıralı adımlar
- initial_input: dict — ilk adım için girdi
- ollama_base_url: string (default: "http://localhost:11434")
- mode: "sequential" | "parallel" | "conditional"
- timeout_seconds: int (default: 30)
- temperature: float (default: 0.7)

Output alanları:
- results: dict[str, str] — {output_key: model_yanıtı}
- pipeline_log: list[{step, model, duration_ms, success}]
- total_duration_ms: int
- failed_steps: list[int]

Pipeline prompt_template içinde değişken:
- {{initial_input.key}} — başlangıç girdisinden
- {{results.step_output_key}} — önceki adım çıktısından

Kurallar:
- httpx.AsyncClient ile Ollama API
- sequential: bir öncekinin çıktısı bir sonrakine gider
- parallel: asyncio.gather, tüm modeller aynı anda
- conditional: önceki adım çıktısına göre sonraki model seç
- timeout aşılırsa step failed, devam et

Bağımlılık: httpx, asyncio

4 dosyayı tam yaz.
Test'lerde: sequential pipeline (mock), parallel (mock),
timeout simülasyonu, template değişken doldurma, başarısız step.
```

---

### Prompt 8-C: ai.fine-tune-prep

```
Skill: ai.fine-tune-prep
Klasör: skills/ai/fine-tune-prep/

Görev:
Ham metin verisini instruction-following
fine-tuning formatına çevirir.

Input alanları:
- raw_data: list[dict] | string — ham veri
- input_type: "qa_pairs" | "conversations" | "text_completion" |
  "classification" | "custom"
- output_format: "alpaca" | "sharegpt" | "jsonl_chat" | "chatml"
- system_prompt: string (opsiyonel)
- train_split: float (default: 0.9) — train/val oranı
- shuffle: bool (default: True)
- max_length_tokens: int (default: 2048) — uzun örnekleri kırp

Output alanları:
- train_jsonl: string — eğitim seti (JSONL)
- val_jsonl: string — validasyon seti (JSONL)
- train_count: int
- val_count: int
- avg_tokens_estimate: int
- format_example: dict — ilk örnek (kontrol için)
- warnings: list[string]

Format örnekleri:
Alpaca: {"instruction": "", "input": "", "output": ""}
ShareGPT: {"conversations": [{"from": "human", "value": ""}, ...]}
ChatML: {"messages": [{"role": "user", "content": ""}, ...]}

Bağımlılık: stdlib (json, random)

4 dosyayı tam yaz.
Test'lerde: alpaca format, sharegpt format, train/val split,
max_length kırpma, shuffle testi.
```

---

### Prompt 8-D: ai.synthetic-data

```
Skill: ai.synthetic-data
Klasör: skills/ai/synthetic-data/

Görev:
Şema ve örnekler verilince Anthropic Claude API
üzerinden sentetik veri seti üretir.

Input alanları:
- schema: dict — üretilecek veri şeması (JSON Schema)
- example_count: int — kaç örnek üretilsin
- domain: string — veri alanı (örn: "tıbbi", "hukuki", "e-ticaret")
- language: "tr" | "en" (default: "tr")
- diversity_level: "low" | "medium" | "high" — çeşitlilik
- seed_examples: list[dict] (opsiyonel) — yönlendirici örnekler
- batch_size: int (default: 10) — her API çağrısında kaç örnek
- anthropic_api_key: string — env'den de okunabilir

Output alanları:
- generated_data: list[dict]
- actual_count: int
- batches_used: int
- failed_batches: int
- schema_compliance_rate: float — üretilen verinin şemaya uyumu

Kurallar:
- anthropic SDK kullan (pip install anthropic)
- API key: önce input'tan, yoksa ANTHROPIC_API_KEY env
- Her batch için prompt: şema + örnekler + miktar
- Response JSON parse et, şema validate et
- Başarısız batch: 2 retry, sonra skip+warning
- Rate limit: batch'ler arası 1sn bekle

Bağımlılık: anthropic, stdlib (json, time)

4 dosyayı tam yaz.
Test'lerde: mock API ile batch üretimi, şema uyumu,
başarısız batch retry, API key env'den okuma, Türkçe veri.
```

---

### Prompt 8-E: ai.embedding-search

```
Skill: ai.embedding-search
Klasör: skills/ai/embedding-search/

Görev:
Metinleri embed eder, cosine similarity ile
en yakın sonuçları bulur. DB gerektirmez.

Input alanları:
- documents: list[{id: str, text: str, metadata: dict}]
- query: string — arama sorgusu
- top_k: int (default: 5)
- model: "sentence-transformers" | "ollama_embed"
- ollama_model: string (default: "nomic-embed-text")
- ollama_base_url: string (default: "http://localhost:11434")
- similarity_threshold: float (default: 0.0) — minimum skor

Output alanları:
- results: list[{id, text, score, metadata, rank}]
- query_embedding_dim: int
- documents_indexed: int
- search_duration_ms: float

Kurallar:
- Embeddingler dict'te tut (in-memory, DB yok)
- sentence-transformers: SentenceTransformer("all-MiniLM-L6-v2")
- ollama: POST /api/embeddings endpoint
- Cosine similarity: numpy dot product / (norm * norm)
- top_k > documents sayısı ise tüm dökümanları döndür
- Boş sorgu → error

Bağımlılık: sentence-transformers veya httpx + numpy

4 dosyayı tam yaz.
Test'lerde: semantic arama, threshold filtresi,
top_k sınırı, Türkçe metin, boş döküman listesi.
```

---

### Prompt 8-F: ai.lang-detect

```
Skill: ai.lang-detect
Klasör: skills/ai/lang-detect/

Görev:
Metni tespit eder, hedef dile çevirir (Ollama tabanlı).

Input alanları:
- text: string — işlenecek metin
- task: "detect" | "translate" | "both"
- target_language: string (opsiyonel) — çeviri için
- ollama_model: string (default: "gemma3:4b")
- ollama_base_url: string (default: "http://localhost:11434")
- confidence_threshold: float (default: 0.7)
- use_heuristics: bool (default: True)
  — Ollama'dan önce basit heuristik dene

Output alanları:
- detected_language: string — "tr", "en", "de" vb.
- detection_confidence: float
- translated_text: string (translate modda)
- detection_method: "heuristic" | "ollama"
- processing_ms: float

Heuristik dil tespiti (Ollama gerektirmez):
- Türkçe: ş, ğ, ü, ö, ı, ç karakterleri
- Almanca: ä, ö, ü, ß
- Fransızca: é, è, ê, ç, à
- Arapça: Unicode range 0600-06FF
- Japonca: Hiragana/Katakana range

Kurallar:
- Önce heuristik dene (hızlı, free)
- Emin değilse (confidence<threshold) Ollama'ya sor
- Çeviri: her zaman Ollama (gemma3 iyi çevirmen)
- Kısa metin (<10 karakter): düşük confidence uyarısı

Bağımlılık: httpx, stdlib (re)

4 dosyayı tam yaz.
Test'lerde: Türkçe heuristik, İngilizce Ollama (mock),
çeviri (mock), kısa metin, karma dil.
```

---

## KATEGORİ 9 — DEVOPS (5 skill)

### Prompt 9-A: devops.dockerfile-gen

```
Skill: devops.dockerfile-gen
Klasör: skills/devops/dockerfile-gen/

Görev:
requirements.txt veya package.json'dan
optimum multi-stage Dockerfile yazar.

Input alanları:
- dependency_file: string — requirements.txt veya package.json içeriği
- file_type: "requirements_txt" | "package_json"
- base_image: string (opsiyonel) — None: otomatik seç
- app_type: "api" | "web" | "worker" | "cli"
- expose_port: int (opsiyonel)
- health_check: bool (default: True)
- non_root_user: bool (default: True) — güvenlik
- use_buildkit: bool (default: True) — cache mount

Output alanları:
- dockerfile: string — tam Dockerfile
- dockerignore: string — .dockerignore içeriği
- base_image_used: string
- stage_count: int — multi-stage sayısı
- estimated_size_mb: int — tahmini image boyutu
- security_notes: list[string]

Multi-stage pattern:
- builder stage: bağımlılıkları kur
- runtime stage: sadece gerekli dosyalar
- Python: python:3.11-slim-bookworm
- Node: node:20-alpine

Kurallar:
- COPY requirements.txt önce (cache için)
- RUN pip install --no-cache-dir
- USER nonroot (non_root_user=True ise)
- HEALTHCHECK: /health endpoint için curl

Bağımlılık: stdlib

4 dosyayı tam yaz.
Test'lerde: Python API, Node web, port expose,
non-root user, health check.
```

---

### Prompt 9-B: devops.github-actions

```
Skill: devops.github-actions
Klasör: skills/devops/github-actions/

Görev:
Proje tipine göre GitHub Actions CI/CD
workflow YAML üretir.

Input alanları:
- project_type: "python" | "node" | "docker" | "mixed"
- workflows: list["test"|"lint"|"build"|"deploy"|"security"|"release"]
- python_versions: list[string] (default: ["3.11","3.12"])
- node_versions: list[string] (default: ["20"])
- deploy_target: "none" | "docker_hub" | "ecr" | "fly_io" | "vps"
- branch_triggers: list[string] (default: ["main","develop"])
- use_cache: bool (default: True)

Output alanları:
- workflows: dict[str, str] — {dosya_adı: YAML içerik}
- workflow_count: int
- jobs_count: int
- secrets_required: list[string] — GITHUB_SECRETS listesi

Workflow şablonları:
- test.yml: pytest / jest / vitest
- lint.yml: ruff/flake8 + eslint/prettier
- build.yml: Docker build + push
- security.yml: bandit, trivy, npm audit
- release.yml: tag tetikli, changelog + GitHub Release

Kurallar:
- actions/checkout@v4, actions/setup-python@v5
- Cache: actions/cache ile pip/npm/pnpm
- Secrets: ${{ secrets.SECRET_NAME }} formatı
- Matrix build: python/node versiyonları için

Bağımlılık: stdlib (yaml benzeri string üretim)

4 dosyayı tam yaz.
Test'lerde: Python test workflow, Docker build,
multi-version matrix, secrets listesi, deploy workflow.
```

---

### Prompt 9-C: devops.nginx-conf

```
Skill: devops.nginx-conf
Klasör: skills/devops/nginx-conf/

Görev:
Domain ve port bilgisinden nginx.conf üretir.

Input alanları:
- domains: list[{
    server_name: str,
    upstream_port: int,
    ssl: bool,
    www_redirect: bool
  }>]
- use_ssl: bool (default: True)
- cert_provider: "certbot" | "self_signed" | "custom"
- proxy_type: "http" | "websocket" | "grpc"
- rate_limiting: bool (default: False)
- requests_per_minute: int (default: 60)
- gzip: bool (default: True)
- cache_static: bool (default: True)
- add_security_headers: bool (default: True)

Output alanları:
- nginx_conf: string — tam nginx.conf
- snippets: dict[str, str] — {snippet_adı: içerik}
  (ssl_params.conf, security_headers.conf vb.)
- certbot_commands: list[string] — SSL için komutlar
- test_command: string — "nginx -t" komutu

Security headers:
- X-Frame-Options, X-Content-Type-Options
- Content-Security-Policy (temel)
- Strict-Transport-Security (HSTS)
- Referrer-Policy

Bağımlılık: stdlib

4 dosyayı tam yaz.
Test'lerde: tek domain HTTP, SSL+certbot, www redirect,
WebSocket proxy, rate limiting.
```

---

### Prompt 9-D: devops.env-secret-scan

```
Skill: devops.env-secret-scan
Klasör: skills/devops/env-secret-scan/

Görev:
Kod tabanında hardcode API key, secret,
token ve credential tespit eder.

Input alanları:
- files: list[{path: str, content: str}]
- scan_types: list["api_keys"|"passwords"|"tokens"|
  "private_keys"|"connection_strings"|"jwt"]
- severity_filter: "all" | "high" | "critical"
- whitelist_patterns: list[string] — görmezden gelme
- context_lines: int (default: 2) — bulguyu çevreleyen satırlar

Output alanları:
- findings: list[{
    file, line, severity, type,
    matched_value_masked, context, recommendation
  }>]
- critical_count: int
- high_count: int
- medium_count: int
- clean_files: int — temiz dosya sayısı
- summary: string — kısa özet

Tespit patternleri (regex):
- AWS: AKIA[0-9A-Z]{16}
- GitHub: ghp_[a-zA-Z0-9]{36}
- Stripe: sk_live_[a-zA-Z0-9]{24}
- JWT: eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+
- Private key: -----BEGIN.*PRIVATE KEY-----
- Generic password: password\s*=\s*["'][^"']{8,}["']
- DB connection: postgresql://user:pass@

Masking: ilk 4 + *** + son 4 karakter

Bağımlılık: stdlib (re)

4 dosyayı tam yaz.
Test'lerde: AWS key tespiti, JWT tespiti, whitelist,
severity filtresi, temiz dosya.
```

---

### Prompt 9-E: devops.nginx-conf için önceki prompt'u kullandık, bu son skill:

### Prompt 9-E: devops.k8s-manifest

```
Skill: devops.k8s-manifest
Klasör: skills/devops/k8s-manifest/

Görev:
Uygulama bilgisinden Kubernetes manifest
YAML dosyaları üretir.

Input alanları:
- app_name: string
- image: string — Docker image (örn: myapp:1.0.0)
- replicas: int (default: 2)
- port: int
- env_vars: dict[str, str] — environment variables
- resources: dict (opsiyonel) — {cpu_request, mem_request, cpu_limit, mem_limit}
- manifests: list["deployment"|"service"|"ingress"|
  "configmap"|"secret"|"hpa"]
- ingress_host: string (opsiyonel)
- namespace: string (default: "default")

Output alanları:
- manifests: dict[str, str] — {manifest_adı: YAML içerik}
- combined_yaml: string — tüm manifest'ler tek dosyada (---)
- resource_count: int
- secrets_detected: list[string] — Secret'a taşınan env var'lar

Kurallar:
- API version: apps/v1 (Deployment), v1 (Service/ConfigMap)
- Deployment: readinessProbe + livenessProbe ekle
- Secret: base64 encode (stdlib base64)
- HPA: minReplicas=2, maxReplicas=10, CPU %70
- Ingress: nginx ingress class
- Hassas env var (PASSWORD, SECRET, KEY, TOKEN) → Secret'a taşı

Bağımlılık: stdlib (base64, yaml string üretim)

4 dosyayı tam yaz.
Test'lerde: Deployment üretimi, Secret env var,
Ingress, HPA, combined YAML.
```

---

## TOPLU ÜRETİM PROMPTU (Hepsini sırayla yazmak için)

```
SkillForge için tüm 50 skill'i sırayla yazacaksın.
Her skill için 4 dosya üreteceksin:
schema.json → worker.py → SKILL.md → test.py

Başlamadan önce onay ver: "Hazırım, hangi skill'den başlayalım?"

Sıra:
1. Önce kategori 1 (UI) tamamla — 5 skill
2. Her skill bittikten sonra "✅ ui.xxx tamamlandı" yaz
3. Bir sonrakine geçmeden önce test.py'nin çalışır
   olduğunu teyit et
4. Tüm dosyaları tek sohbette üret (context'i koru)
5. Sona erdiğinde tüm skill listesini tablo olarak özetle

Dosya başlıklarını mutlaka yaz:
# filepath: skills/ui/bootstrap-scaffold/schema.json

Hazır mısın?
```

---

*Bu prompt dosyası ile Claude Desktop'ta 50 skill'in tamamını
sistematik olarak üretebilirsin. Her kategori için ayrı
oturum açabilir veya toplu üretim promptunu kullanabilirsin.*
