#!/usr/bin/env python3

# NYU CSGY 6903 / 4783
# Spring 2025
# Project 2.6
# Oleksandra Kovalenko, Hirod Nazari, Kritika Naidu, and Josh Hoge
#
# dKI Assessment Tool

import json
import sys
import os


class DKIAssessment:
    def __init__(self):
        # load data from JSON files
        with open("schemes.json", "r") as f:
            self.schemes = json.load(f)

        with open("criteria.json", "r") as f:
            self.criteria = json.load(f)

        with open("weightings.json", "r") as f:
            self.weightings = json.load(f)

        with open("baseline_scheme_scores.json", "r") as f:
            self.baseline_scores = json.load(f)

        with open("stage3_questions.json", "r") as f:
            self.stage3_questions = json.load(f)

        # initialize variables
        self.criteria_rankings = {}
        self.selected_weighting = None
        self.stage2_responses = {1: False, 2: False, 3: False}
        self.stage3_responses = {}
        self.final_scores = {}
        self.assessment_aborted = False

        # create a dictionary to map criteria codes to names
        self.criteria_map = {item["code"]: item["name"] for item in self.criteria}

    def run_assessment(self):
        """run the full assessment process"""
        self.print_header()
        self.stage1_criteria_ranking()
        self.stage2_context_questions()
        self.stage3_additional_questions()
        self.calculate_final_scores()
        self.print_results()
        self.save_assessment_to_json()

    def print_header(self):
        """print the assessment header"""
        print("\nDIGITAL KEY INFRASTRUCTURE (dKI) ASSESSMENT TOOL\n")

        print("This tool helps select a dKI schemes based on the following criteria:")
        for item in self.criteria:
            print(f"Criterion {item['code']}: {item['name']}")

    def stage1_criteria_ranking(self):
        """execute stage 1: Ranking importance of criteria"""
        print("\nSTAGE 1: CRITERIA RANKING\n")

        print(
            "Rank the importance of each criterion on a scale of 1-5 (5 being highest)."
        )
        print("Each ranking may only be used once.\n")

        used_rankings = set()
        for criterion in ["A", "B", "C", "D", "E"]:
            while True:
                try:
                    ranking = int(
                        input(
                            f"Ranking for criterion {criterion} ({self.criteria_map[criterion]}): "
                        )
                    )
                    if ranking < 1 or ranking > 5:
                        print("Please enter a number between 1 and 5.")
                        continue
                    if ranking in used_rankings:
                        print(
                            "This ranking has already been used. Please choose another."
                        )
                        continue
                    used_rankings.add(ranking)
                    self.criteria_rankings[criterion] = ranking
                    break
                except ValueError:
                    print("Please enter a valid number.")

    def stage2_context_questions(self):
        """execute stage 2: Organization context questions"""
        print("\nSTAGE 2: ORGANIZATIONAL CONTEXT\n")

        print("Please answer the following questions about your organization:")

        questions = [
            "My organization has dedicated IT personnel capable of operating and maintaining\n a complex digital key infrastructure system.\n",
            "The digital key infrastructure system selected must support more than 10,000\n users or service more than 10,000 authorizations per minute.\n",
            "My organization operates in a highly-regulated industry and has legal or statutory\n requirements regarding information processing.\n",
        ]

        for i, question in enumerate(questions, 1):
            while True:
                response = input(f"{question} (y/n): ").strip().lower()
                if response in ["y", "n"]:
                    self.stage2_responses[i] = response == "y"
                    break
                else:
                    print("Please enter 'y' or 'n'.")

        # determine the weighting based on the responses
        if not any(self.stage2_responses.values()):
            # no yes responses or checkboxes ticked
            self.selected_weighting = "weighting0"
        elif (
            self.stage2_responses[1]
            and not self.stage2_responses[2]
            and not self.stage2_responses[3]
        ):
            # yes response to question 1 or only checkbox 1 is ticked
            self.selected_weighting = "weighting1"
        elif (
            self.stage2_responses[2]
            and not self.stage2_responses[1]
            and not self.stage2_responses[3]
        ):
            # yes response to question 2 or only checkbox 2 is ticked
            self.selected_weighting = "weighting2"
        elif (
            self.stage2_responses[3]
            and not self.stage2_responses[1]
            and not self.stage2_responses[2]
        ):
            # yes response to question 3 or only checkbox 3 is ticked
            self.selected_weighting = "weighting3"
        elif (
            self.stage2_responses[1]
            and self.stage2_responses[2]
            and not self.stage2_responses[3]
        ):
            # yes responses to questions 1 and 2 or checkboxes 1 and 2 are ticked
            self.selected_weighting = "weighting2"
        elif self.stage2_responses[3] and (
            self.stage2_responses[1] or self.stage2_responses[2]
        ):
            # yes response to one of questions 1 or 2 and yes response to question 3 or combination of (checkboxes 1 or 2) and checkbox 3
            self.selected_weighting = "weighting3"
        elif all(self.stage2_responses.values()):
            # yes response to all three questions or all three checkboxes are ticked
            self.selected_weighting = "weighting3"

    def stage3_additional_questions(self):
        """execute stage 3: Additional yes/no questions"""
        print("\nSTAGE 3: ADDITIONAL QUESTIONS\n")

        print(
            "Please answer the following questions (you may select 'not sure' for up to 2 questions):"
        )
        total_questions = len(self.stage3_questions)
        not_sure_count = 0
        for question in self.stage3_questions:
            q_num = question["stage3_question_number"]
            q_text = question["question_text"]

            while True:
                response = input(f"Q{q_num}: {q_text} (y/n/not sure): ").strip().lower()
                if response in ["y", "n", "not sure"]:
                    if response == "not sure":
                        not_sure_count += 1
                        if not_sure_count > 2:
                            print(
                                "\nError: You have already selected 'not sure' for 2 questions."
                            )
                            print(
                                "Assessment aborted due to excessive 'not sure' responses."
                            )
                            self.stage3_responses[q_num] = (
                                response  # record the third 'not sure'
                            )
                            self.assessment_aborted = True
                            return  # exit the function immediately
                    self.stage3_responses[q_num] = response
                    break
                else:
                    print("Please enter 'y', 'n', or 'not sure'.")

        # check if at least 77% (7/9 rounded down)of questions have definite answers
        definite_answers = sum(
            1 for response in self.stage3_responses.values() if response in ["y", "n"]
        )

        if definite_answers < 0.77 * total_questions:
            print(
                "\nError: At least 77% of questions must have definite (y/n) answers."
            )
            print(
                f"You have answered {definite_answers} out of {total_questions} questions definitely."
            )
            self.assessment_aborted = True
            return

        print("\nResponses to Stage 3 questions:")
        for q_num, response in self.stage3_responses.items():
            print(f"Q{q_num}: {response}")

    def calculate_final_scores(self):
        """calculate the final scores for each scheme"""
        if self.assessment_aborted:
            return

        # initialize score adjustments dictionary with baseline scores
        adjusted_scores = {}
        for scheme_id, scheme_scores in self.baseline_scores.items():
            adjusted_scores[scheme_id] = scheme_scores.copy()

        # apply adjustments based on Stage 3 responses
        for question in self.stage3_questions:
            q_num = question["stage3_question_number"]
            if q_num in self.stage3_responses and self.stage3_responses[q_num] == "y":
                for scheme_id in range(1, 7):
                    scheme_key = f"scheme{scheme_id}"
                    adjustments_key = f"{scheme_key}_adjustments"
                    if adjustments_key in question:
                        for criterion, adjustment in question[adjustments_key].items():
                            curr_value = adjusted_scores[scheme_key][criterion]
                            adjusted_scores[scheme_key][criterion] = max(
                                1, min(6, curr_value + adjustment)
                            )

        # calculate final weighted scores
        for scheme_id in range(1, 7):
            scheme_key = f"scheme{scheme_id}"

            # calculate the weighted scores for each criterion
            weighted_score = 0
            for criterion in [
                "criterionA",
                "criterionB",
                "criterionC",
                "criterionD",
                "criterionE",
            ]:
                criterion_short = criterion[-1]  # Extract just the letter
                raw_score = adjusted_scores[scheme_key][criterion]
                weight = self.weightings[self.selected_weighting][criterion]

                # for negative criteria (D, E), invert the score (7 - score)
                if criterion_short in ["D", "E"]:
                    criterion_score = (7 - raw_score) * weight
                else:
                    criterion_score = raw_score * weight

                weighted_score += criterion_score

            self.final_scores[scheme_key] = {
                "name": self.schemes[scheme_key],
                "adjusted_scores": adjusted_scores[scheme_key],
                "weighted_score": weighted_score,
            }

    def save_assessment_to_json(self):
        """save assessment data to a JSON file with epoch timestamp"""
        import time

        timestamp = int(time.time())
        filename = f"dKI_assessment_{timestamp}.json"

        # create a dictionary with all the assessment data
        assessment_data = {
            "criteria_rankings": self.criteria_rankings,
            "selected_weighting": self.selected_weighting,
            "stage2_responses": self.stage2_responses,
            "stage3_responses": self.stage3_responses,
            "final_scores": self.final_scores,
            "assessment_aborted": self.assessment_aborted,
        }

        # write the data to a JSON file
        with open(filename, "w") as f:
            json.dump(assessment_data, f, indent=4)

        print(f"\nAssessment data saved to {filename}")

    def print_results(self):
        """print the final assessment results"""
        if self.assessment_aborted:
            print("\nASSESSMENT ABORTED")
            print(
                "The assessment was aborted because you did not provide definite answers (y/n) for at least 77% of Stage 3 questions."
            )
            return

        print("\nASSESSMENT RESULTS")

        print("\nFinal scores (weighted and ranked from highest to lowest):")
        ranked_schemes = sorted(
            self.final_scores.items(),
            key=lambda x: x[1]["weighted_score"],
            reverse=True,
        )

        for i, (scheme_id, scheme_data) in enumerate(ranked_schemes, 1):
            print(
                f"{i}. {scheme_data['name']} (Score: {scheme_data['weighted_score']:.2f})"
            )

        print("\nAssessment Aborted: False")

        # print the recommended scheme
        print(f"RECOMMENDED SCHEME: {ranked_schemes[0][1]['name']}")


def main():
    # check if all required files exist
    required_files = [
        "schemes.json",
        "criteria.json",
        "weightings.json",
        "baseline_scheme_scores.json",
        "stage3_questions.json",
    ]

    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("Error: The following required files are missing:")
        for file in missing_files:
            print(f"- {file}")
        sys.exit(1)

    assessment = DKIAssessment()
    try:
        assessment.run_assessment()
    except KeyboardInterrupt:
        print("\nAssessment cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
