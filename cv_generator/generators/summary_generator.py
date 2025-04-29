from ..base_generator import BaseGenerator


class SummaryGenerator(BaseGenerator):
    def __init__(self, vacancy_text, role_descriptions, api_key=None):
        super().__init__(api_key)
        self.vacancy_text = vacancy_text
        self.role_descriptions = role_descriptions

    def generate(self):
        """Generate professional summary."""
        # Collect all text from role descriptions
        all_text = " ".join([desc for descriptions in self.role_descriptions.values() for desc in descriptions])

        summary_prompt = """
        Create a powerful, professional summary for a Unity Developer CV. Model it after this high-quality example:

        EXAMPLE: "Accomplished and empathetic people-first leader known for constructing collaborative cultures and win-win relationships with teammates, partners, clients, and customers. Experienced at developing and deploying strategies to grow new business segments and innovations in retail, e-commerce, hardware, digital distribution, social, and mobile platforms. Highly successful at leading negotiations and closing complex, eight and nine figure contracts that yield increased revenue for all partners."

        For this Unity Developer's summary:

        1. FOCUS ON: Your high-level identity, key character traits, broad expertise areas, and value you bring
        2. INCLUDE: Your specialization (multiplayer development), career arc (5+ years), and what you're known for
        3. HIGHLIGHT: Your approach to development, collaboration style, and technical philosophy
        4. SHOW: How you contribute to business outcomes without specific metrics

        DO NOT:
        - Include specific numbers or percentages (save these for accomplishments)
        - Use generic language like "seeking opportunities"
        - Mention specific company names or products
        - Use bullet points, dashes, or section headings
        - End with a period

        CONTEXT FROM CV:
        {cv_text}

        JOB DESCRIPTION:
        {job_text}

        Length: 250-300 characters maximum. Make every word count.
        """

        # Fix: Use correct variable names in the format method
        formatted_prompt = summary_prompt.format(cv_text=all_text, job_text=self.vacancy_text)

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system",
                     "content": "You create powerful, professional executive summaries that emphasize career identity and value proposition without specific metrics."},
                    {"role": "user", "content": formatted_prompt}
                ],
                model="gpt-4o",
                temperature=0.6
            )
            self.context["ROLE_SUMMARY"] = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating professional summary: {e}")
            self.context[
                "ROLE_SUMMARY"] = "Innovative Unity Developer recognized for crafting high-performance multiplayer experiences and elegant technical solutions. Adept at translating complex requirements into cohesive architecture while mentoring teams toward technical excellence. Committed to creating engaging player experiences through creative problem-solving and meticulous optimization"

        return self.context