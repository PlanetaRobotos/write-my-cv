from ..base_generator import BaseGenerator

class SkillsGenerator(BaseGenerator):
    def __init__(self, vacancy_text, api_key=None):
        super().__init__(api_key)
        self.vacancy_text = vacancy_text

    def generate(self):
        """Generate all skills sections."""
        self.generate_programming_skills()
        self.generate_technical_skills()
        self.generate_soft_skills()
        return self.context

    def generate_programming_skills(self):
        """Generate programming skills section."""
        prompt = (
            "Based on this job description, identify 3-5 most important programming languages, frameworks, and core development skills "
            "and create a concise comma-separated list of them. "
            "Focus on languages, programming paradigms, and fundamental coding concepts. "
            "Example: 'C#, OOP, DOTS, SOLID design patterns, Multithreading, Algorithms' "
            "Don't use bullet points or line breaks. Just provide the comma-separated list. "
            f"Job Description:\n{self.vacancy_text}"
        )

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You identify only the most critical skills for technical resumes."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",
                temperature=0.2
            )
            self.context["ROLE_SKILLS_PROGRAMMING"] = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating programming skills: {e}")
            self.context["ROLE_SKILLS_PROGRAMMING"] = "C#, Unity, Multiplayer frameworks, UniTask, SOLID principles"

    def generate_technical_skills(self):
        """Generate technical skills section."""
        prompt = (
            "Based on this job description, identify 3-5 most important technical skills related to tools, platforms, and specific implementations. "
            "and create a concise comma-separated list of them. "
            "Focus on concrete technical abilities, not programming languages. "
            "Example: 'Server-authoritative architecture, Dependency injection, Performance optimization' "
            "Don't use bullet points or line breaks. Just provide the comma-separated list. "
            f"Job Description:\n{self.vacancy_text}"
        )

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You identify only the most critical technical skills for IT resumes."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",
                temperature=0.2
            )
            self.context["ROLE_SKILLS_TECHNICAL"] = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating technical skills: {e}")
            self.context["ROLE_SKILLS_TECHNICAL"] = "Server-authoritative architecture, Dependency injection (VContainer), Performance optimization"

    def generate_soft_skills(self):
        """Generate soft skills section."""
        prompt = (
            "Based on this job description for this role, "
            "identify only the 5-7 most important soft skills and professional attributes needed for success. "
            "Format as one concise comma-separated list. "
            "Example: 'Collaboration, Communication, Problem-Solving, Attention to Detail, Time Management' "
            f"Job Description:\n{self.vacancy_text}"
        )

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You identify only the most critical soft skills for professional resumes."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",
                temperature=0.2
            )
            self.context["ROLE_SKILLS_SOFT"] = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating soft skills: {e}")
            self.context["ROLE_SKILLS_SOFT"] = "Collaboration, Problem-Solving, Attention to Detail, Time Management, Adaptability" 