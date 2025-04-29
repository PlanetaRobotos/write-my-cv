from ..base_generator import BaseGenerator

class SelfStudyGenerator(BaseGenerator):
    def __init__(self, vacancy_text, api_key=None):
        super().__init__(api_key)
        self.vacancy_text = vacancy_text

    def generate(self):
        """Generate two contextually related self-study entries."""
        self_study_prompt = """
        Create two related self-study entries for a Unity Developer CV. The entries should:
        1. Be complementary to each other (build on the same theme/area)
        2. Focus on technical learning and skill development
        3. Be relevant to the job description
        4. Not include metrics or percentages
        5. Not use bullet points, dashes, or periods at the end
        6. Each entry should be 120 characters or less
        7. Start with an action verb
        8. Focus on practical, hands-on learning

        Format each entry as a single line without any prefixes or suffixes.
        """

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You create concise, technical self-study entries for CVs."},
                    {"role": "user", "content": f"{self_study_prompt}\n\nJob Description:\n{self.vacancy_text}"}
                ],
                model="gpt-4o",
                temperature=0.7
            )

            entries = self._process_response(response)
            
            # Ensure we have exactly two entries
            if len(entries) >= 2:
                self.context["SELF_STUDY_0"] = entries[0]
                self.context["SELF_STUDY_1"] = entries[1]
            else:
                # Fallback entries if generation fails
                self.context["SELF_STUDY_0"] = "Developed multiplayer game prototype using Unity Netcode for GameObjects and Unity Transport"
                self.context["SELF_STUDY_1"] = "Implemented server-authoritative architecture with client-side prediction and lag compensation"

        except Exception as e:
            print(f"Error generating self-study entries: {e}")
            # Fallback entries
            self.context["SELF_STUDY_0"] = "Developed multiplayer game prototype using Unity Netcode for GameObjects and Unity Transport"
            self.context["SELF_STUDY_1"] = "Implemented server-authoritative architecture with client-side prediction and lag compensation"

        return self.context 