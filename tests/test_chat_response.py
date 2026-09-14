import unittest

from chat_response import response_issues, safe_fallback


AWS_QUESTION = "Quelle est votre expérience sur AWS ?"
AWS_OBSERVED = """Chez EssilorLuxottica (juin 2019 – décembre 2024), Lionel a piloté,
en tant que Product Owner, l'évolution d'une API de stockage de données sensibles
vers une architecture AWS multi-région [C17, T07, E04].
Ce qu'il convient de préciser sur le périmètre : il s'agit d'un rôle de pilotage
produit et de coordination de réalisation, pas de la conception ou du développement
technique personnel de l'infrastructure AWS. Aucun SLA chiffré n'est associé à cette expérience.
"""


class ChatResponseTests(unittest.TestCase):
    def test_observed_aws_answer_has_targeted_voice_reference_and_scope_issues(self):
        issues = response_issues(AWS_QUESTION, AWS_OBSERVED)
        self.assertIn("third_person", issues)
        self.assertIn("internal_references", issues)
        self.assertIn("unsolicited_caveat", issues)

    def test_observed_contradictory_certification_answer_is_rejected(self):
        answer = ("Je ne détiens pas la certification AWS Certified Solutions Architect Professional. "
                  "Je ne peux pas confirmer ce point avec les informations disponibles.")
        self.assertIn("credential_absence", response_issues(
            "Détenez-vous la certification AWS Certified Solutions Architect Professional ?", answer))

    def test_credential_absence_variants_in_both_languages(self):
        for answer in ("Je ne possède pas cette certification.", "Je n'ai pas cette certification.",
                       "Je n’ai aucune certification AWS.", "Je ne dispose pas de cette certification.",
                       "Je ne suis pas certifié AWS.", "I don't hold that certification.",
                       "I do not have this credential.", "I have no AWS certification.",
                       "I'm not certified in AWS.", "I am uncertified on AWS."):
            with self.subTest(answer=answer):
                self.assertIn("credential_absence", response_issues("AWS?", answer))

    def test_positive_and_unknown_credentials_remain_valid(self):
        for answer in ("Je possède la certification AWS Cloud Practitioner.",
                       "Je ne peux pas confirmer la détention de cette certification.",
                       "Cette certification n'est pas renseignée dans les informations disponibles.",
                       "I can't confirm whether I hold that certification.",
                       "I have the AWS Cloud Practitioner certification."):
            with self.subTest(answer=answer):
                self.assertEqual(response_issues("Vos certifications ?", answer), [])

    def test_general_aws_scope_caveats_in_both_languages(self):
        cases = ((AWS_QUESTION, "Mon rôle était le pilotage produit, pas le développement technique."),
                 ("What is your experience with AWS?", "My role was product ownership rather than technical implementation."),
                 ("What is your experience with AWS?", "I don't have documented experience in AWS administration."))
        for question, answer in cases:
            with self.subTest(answer=answer):
                self.assertIn("unsolicited_caveat", response_issues(question, answer))

    def test_explicit_or_compound_questions_allow_scope_limitations(self):
        for question in ("Avez-vous personnellement conçu l'architecture AWS ?",
                         "What is your experience with AWS administration?",
                         "Quelle est votre expérience sur AWS et quelles sont vos limites ?",
                         "What is your experience with AWS? Did you personally code it?"):
            with self.subTest(question=question):
                self.assertNotIn("unsolicited_caveat", response_issues(question,
                    "My role was product ownership rather than technical implementation."))

    def test_ai_disclosure_and_factual_coordination_are_not_rejected(self):
        for answer in ("Je suis l'assistant IA de Lionel Tchamfong. Je présente son parcours réel.",
                       "I'm Lionel Tchamfong's AI assistant.",
                       "Chez EssilorLuxottica, j'ai piloté une API AWS multi-région et coordonné les pentests.",
                       "I coordinated security testing with the cybersecurity team."):
            with self.subTest(answer=answer):
                self.assertEqual(response_issues(AWS_QUESTION, answer), [])

    def test_only_internal_citation_brackets_are_rejected(self):
        for reference in ("[C17, T07, E04]", "[D05]", "[K6a6972610001]", "[L05; U02]"):
            with self.subTest(reference=reference):
                self.assertIn("internal_references", response_issues("AWS?", "J'ai piloté cela " + reference))
        for prose in ("J'ai utilisé des instances C7g et EC2.", "Sur la période [2019–2024].",
                      "Le niveau [B2] est mentionné.", "J'ai utilisé AWS [cloud]."):
            self.assertEqual(response_issues("AWS?", prose), [])

    def test_fallback_is_first_person_uncertainty_in_requested_language(self):
        self.assertTrue(safe_fallback("fr").startswith("Je ne peux pas confirmer"))
        self.assertTrue(safe_fallback("en").startswith("I can't confirm"))
        self.assertEqual(response_issues("Une certification ?", safe_fallback("fr")), [])
        self.assertEqual(response_issues("A certification?", safe_fallback("en")), [])


if __name__ == "__main__":
    unittest.main()
