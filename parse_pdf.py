import os
import re
import pandas as pd
import pdfplumber
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path

class CurriculumParser:
    def __init__(self, pdf_dir: str):
        """
        Инициализация парсера учебных планов
        
        Args:
            pdf_dir: Директория с PDF-файлами учебных планов
        """
        self.pdf_dir = pdf_dir
        self.dir_name = os.path.basename(os.path.normpath(pdf_dir))
        self.curriculum_data = {}
        
    def parse_all_files(self) -> Dict[str, Any]:
        """
        Парсинг всех PDF-файлов из указанной директории
        
        Returns:
            Словарь с структурированными данными всех учебных планов
        """
        if not os.path.exists(self.pdf_dir):
            print(f"Директория {self.pdf_dir} не существует")
            return self.curriculum_data
                
        pdf_files = [f for f in os.listdir(self.pdf_dir) if f.lower().endswith('.pdf')]
        
        for pdf_file in pdf_files:
            file_path = os.path.join(self.pdf_dir, pdf_file)
            program_name = self._extract_program_name(pdf_file)
            
            print(f"Обработка файла: {file_path}")
            try:
                curriculum_data = self._parse_pdf(file_path)
                self.curriculum_data[program_name] = curriculum_data
            except Exception as e:
                print(f"Ошибка при обработке файла {file_path}: {e}")
        
        return self.curriculum_data
    
    def _extract_program_name(self, filename: str) -> str:
        """
        Извлекает название программы из имени файла
        
        Args:
            filename: Имя файла
        
        Returns:
            Название программы
        """
        # Удаляем расширение и заменяем подчеркивания пробелами
        name = os.path.splitext(filename)[0].replace('_', ' ')
        return name
    
    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Парсит PDF-файл с учебным планом
        
        Args:
            file_path: Путь к PDF-файлу
        
        Returns:
            Структурированные данные учебного плана
        """
        result = {
            "program_info": {},
            "semesters": {}
        }
        
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            
            # Извлекаем текст из всех страниц
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            
            # Извлекаем информацию о программе
            result["program_info"] = self._extract_program_info(full_text)
            
            # Извлекаем информацию о семестрах и дисциплинах
            result["semesters"] = self._extract_semesters_and_courses(full_text)
        
        return result
    
    def _extract_program_info(self, text: str) -> Dict[str, str]:
        """
        Извлекает общую информацию о программе
        
        Args:
            text: Текст из PDF-файла
        
        Returns:
            Словарь с информацией о программе
        """
        info = {}
        
        # Извлекаем название программы
        program_name_match = re.search(r"Программа[:\s]+([^\n]+)", text, re.IGNORECASE)
        if program_name_match:
            info["name"] = program_name_match.group(1).strip()
        
        # Извлекаем направление подготовки
        direction_match = re.search(r"Направление[:\s]+([^\n]+)", text, re.IGNORECASE)
        if direction_match:
            info["direction"] = direction_match.group(1).strip()
        
        # Извлекаем уровень образования
        level_match = re.search(r"Уровень[:\s]+([^\n]+)", text, re.IGNORECASE)
        if level_match:
            info["level"] = level_match.group(1).strip()
        
        # Извлекаем общую трудоемкость
        credits_match = re.search(r"(?:Трудоемкость|Общая трудоемкость)[:\s]+(\d+)", text, re.IGNORECASE)
        if credits_match:
            info["total_credits"] = int(credits_match.group(1).strip())
        
        return info
    
    def _extract_semesters_and_courses(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Извлекает информацию о семестрах и учебных дисциплинах
        
        Args:
            text: Текст из PDF-файла
        
        Returns:
            Словарь с информацией о дисциплинах по семестрам
        """
        semesters = {}
        
        # Ищем блоки с семестрами
        semester_blocks = re.finditer(r"(?:Пул\s+(?:выборных\s+)?дисциплин\.?\s+)?(\d+)\s+семестр[\s\S]*?(?=(?:\d+\s+семестр|$))", text)
        
        for block_match in semester_blocks:
            block_text = block_match.group(0)
            semester_num = block_match.group(1)
            
            # Извлекаем строки с дисциплинами
            # Предполагаем, что строка с дисциплиной имеет формат:
            # [номер] [название дисциплины] [кредиты] [часы]
            courses = []
            
            # Несколько вариантов паттернов для разных форматов
            patterns = [
                r"(\d+)\s+([^\d]+?)\s+(\d+)\s+(\d+)",  # [номер] [название] [кредиты] [часы]
                r"([^\d]+?)\s+(\d+)\s+(\d+)$"          # [название] [кредиты] [часы]
            ]
            
            for line in block_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                course_info = None
                
                # Пробуем разные паттерны
                for pattern in patterns:
                    matches = re.search(pattern, line)
                    if matches:
                        groups = matches.groups()
                        if len(groups) == 4:  # [номер] [название] [кредиты] [часы]
                            course_info = {
                                "number": groups[0],
                                "name": groups[1].strip(),
                                "credits": int(groups[2]),
                                "hours": int(groups[3])
                            }
                        elif len(groups) == 3:  # [название] [кредиты] [часы]
                            course_info = {
                                "name": groups[0].strip(),
                                "credits": int(groups[1]),
                                "hours": int(groups[2])
                            }
                        break
                
                if course_info:
                    courses.append(course_info)
            
            semesters[semester_num] = courses
        
        return semesters
    
    def save_to_json(self, output_file: str = None):
        """
        Сохраняет структурированные данные в JSON-файл
        
        Args:
            output_file: Путь к файлу для сохранения результатов
        """
        if output_file is None:
            output_file = f"curriculum_data_{self.dir_name}.json"
            
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.curriculum_data, f, ensure_ascii=False, indent=4)
        
        print(f"Данные сохранены в файл: {output_file}")
    
    def get_llm_friendly_format(self) -> str:
        """
        Преобразует данные в удобный для LLM формат
        
        Returns:
            Строка с форматированными данными для передачи в LLM
        """
        result = []
        
        result.append(f"# Учебный план: {self.dir_name}")
        result.append(f"Директория: {self.pdf_dir}")
        result.append("")
        
        for program, data in self.curriculum_data.items():
            result.append(f"## Программа: {program}")
            
            if "program_info" in data and data["program_info"]:
                result.append("\n### Информация о программе:")
                for key, value in data["program_info"].items():
                    result.append(f"- {key.replace('_', ' ').title()}: {value}")
            
            if "semesters" in data and data["semesters"]:
                for semester, courses in data["semesters"].items():
                    result.append(f"\n### Семестр {semester}:")
                    
                    if not courses:
                        result.append("Нет информации о дисциплинах")
                        continue
                    
                    # Создаем таблицу для дисциплин
                    result.append("\n| № | Дисциплина | Кредиты | Часы |")
                    result.append("| --- | --- | --- | --- |")
                    
                    for i, course in enumerate(courses):
                        course_num = course.get("number", str(i+1))
                        name = course.get("name", "Н/Д")
                        credits = course.get("credits", "Н/Д")
                        hours = course.get("hours", "Н/Д")
                        
                        result.append(f"| {course_num} | {name} | {credits} | {hours} |")
            
            result.append("\n---\n")
        
        return "\n".join(result)
    
    def create_dataframe(self) -> pd.DataFrame:
        """
        Создает DataFrame с данными о дисциплинах из всех программ
        
        Returns:
            DataFrame с данными о дисциплинах
        """
        rows = []
        
        for program, data in self.curriculum_data.items():
            if "semesters" in data:
                for semester, courses in data["semesters"].items():
                    for course in courses:
                        row = {
                            "Directory": self.dir_name,
                            "Program": program,
                            "Semester": semester,
                            "Course Name": course.get("name", ""),
                            "Credits": course.get("credits", 0),
                            "Hours": course.get("hours", 0)
                        }
                        rows.append(row)
        
        return pd.DataFrame(rows)
    
    def save_to_csv(self, output_file: str = None):
        """
        Сохраняет данные о дисциплинах в CSV-файл
        
        Args:
            output_file: Путь к файлу для сохранения результатов
        """
        if output_file is None:
            output_file = f"curriculum_courses_{self.dir_name}.csv"
            
        df = self.create_dataframe()
        df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"Данные сохранены в CSV-файл: {output_file}")
        
        return df

def process_curriculum_directory(directory: str):
    """
    Обрабатывает директорию с PDF-файлами учебных планов
    
    Args:
        directory: Путь к директории
    
    Returns:
        Кортеж (DataFrame, str) с данными курсов и LLM-форматированным текстом
    """
    print(f"\n{'='*50}")
    print(f"Обрабатываем директорию: {directory}")
    print(f"{'='*50}\n")
    
    parser = CurriculumParser(directory)
    
    # Парсим все файлы
    data = parser.parse_all_files()
    
    # Если данных нет, возвращаем пустые результаты
    if not data:
        print(f"В директории {directory} не найдены данные.")
        return pd.DataFrame(), ""
    
    # Сохраняем результаты в JSON
    parser.save_to_json()
    
    # Получаем данные в формате для LLM
    llm_format = parser.get_llm_friendly_format()
    
    # Сохраняем LLM-форматированные данные
    dir_name = os.path.basename(os.path.normpath(directory))
    with open(f"curriculum_for_llm_{dir_name}.md", "w", encoding="utf-8") as f:
        f.write(llm_format)
    
    # Сохраняем в CSV и возвращаем DataFrame
    df = parser.save_to_csv()
    
    return df, llm_format

def combine_dataframes(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Объединяет несколько DataFrame в один
    
    Args:
        dataframes: Список DataFrame для объединения
    
    Returns:
        Объединенный DataFrame
    """
    if not dataframes:
        return pd.DataFrame()
    
    return pd.concat(dataframes, ignore_index=True)

# Пример использования
if __name__ == "__main__":
    # Указываем директории с PDF-файлами
    pdf_directories = ["./pdf_curriculum_ai", "./pdf_curriculum_ai_product"]
    
    # Список для хранения результатов по каждой директории
    all_dataframes = []
    all_llm_formats = []
    
    # Обрабатываем каждую директорию отдельно
    for directory in pdf_directories:
        df, llm_format = process_curriculum_directory(directory)
        if not df.empty:
            all_dataframes.append(df)
            all_llm_formats.append(llm_format)
    
    # Объединяем все данные
    combined_df = combine_dataframes(all_dataframes)
    
    # Если есть данные, сохраняем общую сводку
    if not combined_df.empty:
        # Сохраняем объединенный CSV
        combined_df.to_csv("curriculum_all_courses.csv", index=False, encoding="utf-8")
        print("\nВсе данные объединены в файл: curriculum_all_courses.csv")
        
        # Выводим статистику
        print("\nСтатистика по программам и директориям:")
        program_stats = combined_df.groupby(["Directory", "Program"]).agg({
            "Course Name": "count",
            "Credits": "sum"
        }).rename(columns={"Course Name": "Количество дисциплин", "Credits": "Общая трудоемкость"})
        
        print(program_stats)
        
        # Сохраняем сводную статистику
        program_stats.to_csv("curriculum_summary_stats.csv", encoding="utf-8")
        print("\nСводная статистика сохранена в файл: curriculum_summary_stats.csv")
        
        # Создаем сводную таблицу по семестрам
        semester_summary = combined_df.pivot_table(
            index=["Directory", "Program"], 
            columns="Semester", 
            values="Credits", 
            aggfunc="sum",
            fill_value=0
        )
        
        # Сохраняем сводную таблицу
        semester_summary.to_csv("curriculum_semester_summary.csv", encoding="utf-8")
        print("\nСводка по семестрам сохранена в файл: curriculum_semester_summary.csv")
        
        # Объединяем все LLM-форматированные тексты и сохраняем в один файл
        combined_llm = "\n\n".join(all_llm_formats)
        with open("curriculum_all_programs_for_llm.md", "w", encoding="utf-8") as f:
            f.write(combined_llm)
        print("\nВсе данные для LLM объединены в файл: curriculum_all_programs_for_llm.md")
    else:
        print("\nНет данных для объединения. Проверьте указанные директории.")
