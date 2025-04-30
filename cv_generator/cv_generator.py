from docxtpl import DocxTemplate
from docx2pdf import convert
import os
import re
from .generators.role_generator import RoleGenerator
from .generators.skills_generator import SkillsGenerator
from .generators.summary_generator import SummaryGenerator
from .generators.self_study_generator import SelfStudyGenerator

class CVGenerator:
    def __init__(self, vacancy_text_path="vacancy_description.txt", template_path="CV_template.docx"):
        self.vacancy_text = self._load_vacancy_text(vacancy_text_path)
        self.template_path = template_path
        self.context = {}
        self.role_descriptions = {}
        self.selected_role_keywords = {}

        # Initialize default role information
        self._init_default_info()

    def _load_vacancy_text(self, path):
        """Load the vacancy description text."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Vacancy description file not found at {path}")
            return ""

    def _init_default_info(self):
        """Initialize default role information dictionary."""
        self.default_info = {
            "LUCID": (
                "Architected and implemented an adaptive AI-driven prompting system for a VR app serving autistic children, resulting in 40% increased session duration and measurably improved learning outcomes across key metrics, "
                "Developed asynchronous programming patterns for the VR app's third-party SDK integrations, ensuring smooth interaction between different system components"
            ),
            "GALAXY": (
                "Engineered high-performance, scalable gameplay features in C# for multi-platform titles, resulting an increase in player retention and successful deployment across mobile platforms, "
                "Designed and implemented a comprehensive UI architecture using MVVM pattern that reduced iteration time by ~30% and enabled artists to modify interfaces without programmer intervention, "
                "Optimized rendering pipelines and memory management systems that improved frame rates on low-end mobile devices, "
                "Established code quality standards and review processes that reduced critical bugs in production builds while mentoring junior developers on optimization techniques"
            ),
            "WHIMSY": (
                "Architected core networking systems for a multiplayer game with focus on profiling and optimizing GPU/CPU performance to support concurrent players, "
                "Integrated third-party SDKs (analytics, ads, IAP) into the game ecosystem while maintaining performance standards on mobile platform requirements"
            ),
            "APPSIDE": (
                "Engineered reusable component systems using advanced C# techniques while adhering to OOP principles and SOLID design patterns, "
                "Developed performance-optimized systems for mobile games with careful attention to memory usage and battery efficiency"
            ),
            "WOUFF": (
                "Optimized critical rendering systems with URP, improving overall performance while maintaining visual quality, "
                "Implemented responsive UI frameworks that automatically adapted to different screen resolutions and aspect ratios across mobile platform requirements"
            )
        }

        # Define role configurations
        self.roles_config = {
            "LUCID": {"count": 2, "tech_skills": False},
            "GALAXY": {"count": 4, "tech_skills": True},
            "WHIMSY": {"count": 2, "tech_skills": True},
            "APPSIDE": {"count": 2, "tech_skills": False},
            "WOUFF": {"count": 2, "tech_skills": False},
        }

    def show_menu(self):
        """Display the interactive menu and handle user selection."""
        print("\n=== CV Generation Menu ===")
        print("Select sections to generate (comma-separated numbers or 'all'):")
        print("1. Role Descriptions")
        print("2. Skills Sections")
        print("3. Professional Summary")
        print("4. Self-Study Entries")
        print("5. All Sections")
        print("0. Exit")
        
        while True:
            try:
                choice = input("\nYour choice: ").strip().lower()
                
                if choice == '0':
                    return False
                elif choice == 'all' or choice == '5':
                    return self.generate_all_sections()
                else:
                    # Parse comma-separated numbers
                    sections = [int(x.strip()) for x in choice.split(',') if x.strip()]
                    if not sections:
                        print("Invalid input. Please enter numbers separated by commas or 'all'.")
                        continue
                    
                    return self.generate_selected_sections(sections)
                    
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas or 'all'.")
                continue

    def generate_selected_sections(self, sections):
        """Generate only the selected sections of the CV."""
        print("\nGenerating selected sections...")
        
        # Track if we need to render the template at the end
        needs_rendering = False
        
        if 1 in sections:
            print("\nGenerating cohesive role descriptions...")
            role_generator = RoleGenerator(self.vacancy_text, self.default_info, self.roles_config)
            self.role_descriptions, self.selected_role_keywords = role_generator.generate()
            self.context.update(role_generator.context)
            needs_rendering = True
            
        if 2 in sections:
            print("\nGenerating skills sections...")
            skills_generator = SkillsGenerator(self.vacancy_text)
            self.context.update(skills_generator.generate())
            needs_rendering = True
            
        if 3 in sections:
            print("\nGenerating professional summary...")
            summary_generator = SummaryGenerator(self.vacancy_text, self.role_descriptions)
            self.context.update(summary_generator.generate())
            needs_rendering = True
            
        if 4 in sections:
            print("\nGenerating self-study entries...")
            self_study_generator = SelfStudyGenerator(self.vacancy_text)
            self.context.update(self_study_generator.generate())
            needs_rendering = True
            
        if needs_rendering:
            print("\nRendering CV template...")
            self.render_template()
            
        return True

    def generate_all_sections(self):
        """Generate all sections of the CV."""
        print("\nGenerating all sections...")
        
        # Generate role descriptions first as other sections depend on it
        role_generator = RoleGenerator(self.vacancy_text, self.default_info, self.roles_config)
        self.role_descriptions, self.selected_role_keywords = role_generator.generate()
        self.context.update(role_generator.context)
        
        # Generate other sections
        skills_generator = SkillsGenerator(self.vacancy_text)
        self.context.update(skills_generator.generate())
        
        summary_generator = SummaryGenerator(self.vacancy_text, self.role_descriptions)
        self.context.update(summary_generator.generate())
        
        self_study_generator = SelfStudyGenerator(self.vacancy_text)
        self.context.update(self_study_generator.generate())
        
        self.render_template()
        return True

    def render_template(self, output_docx_path="CV.docx", output_pdf_path="CV_final.pdf"):
        """Render the DOCX template and convert to PDF if needed."""
        try:
            # Check if file is available for writing
            while True:
                try:
                    with open(output_docx_path, 'w') as f:
                        pass
                    break
                except IOError:
                    print(f"\nThe file {output_docx_path} is currently in use.")
                    print("Please close the file and press Enter to continue...")
                    input()
                    continue

            # Create a modified context with appropriate styling for docxtpl
            styled_context = {}
            for key, value in self.context.items():
                if isinstance(value, str) and "<BOLD>" in value:
                    # Replace <BOLD> tags with docxtpl's rich text format
                    styled_text = []
                    parts = re.split(r'(<BOLD>.*?</BOLD>)', value)

                    for part in parts:
                        if part.startswith('<BOLD>') and part.endswith('</BOLD>'):
                            # Extract text between tags
                            bold_text = re.sub(r'<BOLD>(.*?)</BOLD>', r'\1', part)
                            styled_text.append({'text': bold_text, 'bold': True})
                        elif part:
                            styled_text.append({'text': part})

                    styled_context[key] = styled_text
                else:
                    styled_context[key] = value

            # Render template with styled context
            from docxtpl import DocxTemplate, RichText

            doc = DocxTemplate(self.template_path)

            # Convert styled_context entries to RichText objects
            for key, value in styled_context.items():
                if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                    rt = RichText()
                    for item in value:
                        if item.get('bold', False):
                            rt.add(item['text'], bold=True)
                        else:
                            rt.add(item['text'])
                    styled_context[key] = rt

            doc.render(styled_context)
            doc.save(output_docx_path)
            print(f"CV successfully saved as {output_docx_path}")

        except Exception as e:
            print(f"Error rendering template: {e}")
            import traceback
            traceback.print_exc()

    def generate_cv(self):
        """Generate CV content based on user selection."""
        return self.show_menu() 