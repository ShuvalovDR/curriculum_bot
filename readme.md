## Супер быстрая реализация бота для ответа на вопросы абитуриентов.

### Идея:

1. Скачать и распарсить pdf файлы с учебным планом.
2. Написать промпт GPT модельке, чтобы модель вела себя как куратор / консультант вуза. Возможность общатся с ней по API.
3. Скорее всего абитуриент будет спрашивать про учебный план и куда ему лучше  из двух направлений, поэтому в промпт надо через RAG прокидывать контекст учебного плана одного и второго направления и отдавать ему на сравнение (предметы семестр и прочее). Запретить ему отвечать на что угодно кроме вопросов о поступлении (сказано в задании). `BERT` моделью с hf + `RANK25BM` искать похожую семантику и слова с названиями предметов (у бота будет контекст в 5 строк из учебного плана одного предмета и 5 строк из другого), так что у нее будет досататчно контекста чтобы отвечать на вопросы про предметы.
4. Реализовать общение через ТГ.

### Реализация
1. `bot.py` - файл с ботом
2. `parse_pdf.py` - парсинг учебного плана (pdf2csv)
3. `llm_api.py` - RAG + model api generate function
4. `download_curriculums.py` - скачать учебные планы

### Как запустить:
1. Создать в директории .env файл, написать туда токены для бота и LLM. В качестве прокси я использую https://aitunnel.ru/ для доступа ко многим моделям. LLM_KEY - токен с сайта.
```
LLM_KEY="<OPENAI-KEY>"
SUPER_BOT_KEY="<BOT-KEY>"
BASE_URL="https://api.aitunnel.ru/v1/"
```
2. Установить библиотки (мб что-то пропустил)
Торч с GPU
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
Другие либы:
```bash
pip install \ 
aiogram==3.20.0.post0 \
faiss-cpu==1.11.0 \
fastapi==0.115.12 \
huggingface-hub==0.31.1 \
langchain==0.3.25 \
langchain-community==0.3.23 \
langchain-core==0.3.59 \
langchain-huggingface==0.2.0 \
langchain-openai==0.3.17 \
langchain-redis==0.2.1 \
langgraph==0.3.34 \
langsmith==0.3.42 \
numpy==1.26.4 \
openai==1.79.0 \
pydantic==2.11.4 \
python-dotenv==1.1.0 \
rank-bm25==0.2.2 \
redis==5.3.0 \
scikit-learn==1.6.1 \
scipy==1.15.3 \
sentence-transformers==4.1.0 \
transformers==4.51.3 \
uvicorn==0.34.2 \
selenium \
pdfplumber \
beautifulsoup4
```
3. Чтобы скачать учебные планы с сайтов https://abit.itmo.ru/program/master/ai_product и https://abit.itmo.ru/program/master/ai запустить
```bash
python download_curriculums.py
```
4. Распарсить скачанные pdf (получатся csv и third party файлы). По факту сейчас в текущую директорию все скачивается, надо исправить.
```bash
python parse_pdf.py
```
5. Запускаем бота:
```bash
python bot.py
```

