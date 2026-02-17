#!/usr/bin/env python3

# NYU CSGY 6903 / 4783
# Spring 2025
# Project 2.6
# Oleksandra Kovalenko, Hirod Nazari, Kritika Naidu, and Josh Hoge
#
# Monte Carlo simulation for dKI Assessment Tool
# invoke with 'montecarlo.py --trials <NUMBER_OF_TRIALS>'


import json
import random
import time
import os
import copy
from collections import Counter


class DKIMonteCarloSimulation:
    def __init__(self, num_trials=1000):
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
        self.num_trials = num_trials
        self.results = []

        # create a dictionary to map criteria codes to names
        self.criteria_map = {item["code"]: item["name"] for item in self.criteria}

    def run_simulation(self):
        """run the Monte Carlo simulation"""
        print(f"Running {self.num_trials} simulations...")
        start_time = time.time()

        for trial in range(self.num_trials):
            result = self.run_single_trial()
            if result:  # only add if not aborted
                self.results.append(result)

            # print progress every 10% of trials
            if (trial + 1) % max(1, self.num_trials // 10) == 0:
                progress = (trial + 1) / self.num_trials * 100
                elapsed = time.time() - start_time
                print(
                    f"Progress: {progress:.1f}% ({trial + 1}/{self.num_trials}), Elapsed time: {elapsed:.2f}s"
                )

        # analyze and print results
        self.analyze_results()

    def run_single_trial(self):
        """run a single trial with randomized responses"""
        # initialize trial data
        criteria_rankings = {}
        stage2_responses = {1: False, 2: False, 3: False}
        stage3_responses = {}

        # Stage 1: random criteria rankings (1-5, each used once)
        rankings = list(range(1, 6))
        random.shuffle(rankings)
        for i, criterion in enumerate(["A", "B", "C", "D", "E"]):
            criteria_rankings[criterion] = rankings[i]

        # Stage 2: random context responses
        for i in range(1, 4):
            stage2_responses[i] = random.choice([True, False])

        # determine the weighting based on the responses
        if not any(stage2_responses.values()):
            # no yes responses or checkboxes ticked
            selected_weighting = "weighting0"
        elif (
            stage2_responses[1] and not stage2_responses[2] and not stage2_responses[3]
        ):
            # yes response to question 1 or only checkbox 1 is ticked
            selected_weighting = "weighting1"
        elif (
            stage2_responses[2] and not stage2_responses[1] and not stage2_responses[3]
        ):
            # yes response to question 2 or only checkbox 2 is ticked
            selected_weighting = "weighting2"
        elif (
            stage2_responses[3] and not stage2_responses[1] and not stage2_responses[2]
        ):
            # yes response to question 3 or only checkbox 3 is ticked
            selected_weighting = "weighting3"
        elif stage2_responses[1] and stage2_responses[2] and not stage2_responses[3]:
            # yes responses to questions 1 and 2 or checkboxes 1 and 2 are ticked
            selected_weighting = "weighting2"
        elif stage2_responses[3] and (stage2_responses[1] or stage2_responses[2]):
            # yes response to one of questions 1 or 2 and yes response to question 3 or combination of (checkboxes 1 or 2) and checkbox 3
            selected_weighting = "weighting3"
        elif all(stage2_responses.values()):
            # yes response to all three questions or all three checkboxes are ticked
            selected_weighting = "weighting3"

        # Stage 3: Random yes/no/not sure responses
        # randomly decide how many "not sure" responses (0, 1, or 2)
        not_sure_count = random.choice([0, 1, 2])

        # randomly select which questions will be "not sure"
        if not_sure_count > 0:
            not_sure_questions = random.sample(
                range(1, len(self.stage3_questions) + 1), not_sure_count
            )
        else:
            not_sure_questions = []

        for question in self.stage3_questions:
            q_num = question["stage3_question_number"]
            if q_num in not_sure_questions:
                stage3_responses[q_num] = "not sure"
            else:
                stage3_responses[q_num] = random.choice(["y", "n"])

        # check if at least 77% (7/9 rounded down)of questions have definite answers
        definite_answers = sum(
            1 for response in stage3_responses.values() if response in ["y", "n"]
        )
        total_questions = len(self.stage3_questions)

        if definite_answers < 0.77 * total_questions:
            # assessment would be aborted, skip this trial
            return None

        # calculate final scores
        adjusted_scores = {}
        for scheme_id, scheme_scores in self.baseline_scores.items():
            adjusted_scores[scheme_id] = scheme_scores.copy()

        # apply adjustments based on Stage 3 responses
        for question in self.stage3_questions:
            q_num = question["stage3_question_number"]
            if q_num in stage3_responses and stage3_responses[q_num] == "y":
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
        final_scores = {}
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
                weight = self.weightings[selected_weighting][criterion]

                # for negative criteria (D, E), invert the score (7 - score)
                if criterion_short in ["D", "E"]:
                    criterion_score = (7 - raw_score) * weight
                else:
                    criterion_score = raw_score * weight

                weighted_score += criterion_score

            final_scores[scheme_key] = {
                "name": self.schemes[scheme_key],
                "adjusted_scores": adjusted_scores[scheme_key],
                "weighted_score": weighted_score,
            }

        # determine the winning scheme
        ranked_schemes = sorted(
            final_scores.items(), key=lambda x: x[1]["weighted_score"], reverse=True
        )
        winning_scheme = ranked_schemes[0][0]

        return {
            "criteria_rankings": criteria_rankings,
            "stage2_responses": stage2_responses,
            "selected_weighting": selected_weighting,
            "stage3_responses": stage3_responses,
            "final_scores": final_scores,
            "winning_scheme": winning_scheme,
            "winning_scheme_name": self.schemes[winning_scheme],
        }

    def analyze_results(self):
        """analyze and print the simulation results"""
        if not self.results:
            print("No valid results to analyze. All trials were aborted.")
            return

        print(f"\nMONTE CARLO SIMULATION RESULTS ({len(self.results)} valid trials)")

        # count winning schemes
        scheme_counts = Counter(result["winning_scheme"] for result in self.results)

        print("Winning scheme distribution:")
        print("-" * 60)
        print(f"{'Scheme':<30} | {'Count':<10} | {'Percentage':<10}")
        print("-" * 60)

        for scheme_id in sorted(scheme_counts.keys()):
            count = scheme_counts[scheme_id]
            percentage = (count / len(self.results)) * 100
            scheme_name = self.schemes[scheme_id]
            print(f"{scheme_name:<30} | {count:<10} | {percentage:.2f}%")

        # check if any scheme was never selected
        never_selected = [
            scheme_name
            for scheme_id, scheme_name in self.schemes.items()
            if scheme_id not in scheme_counts
        ]

        if never_selected:
            print("\nThe following schemes were NEVER selected:")
            for scheme_name in never_selected:
                print(f"- {scheme_name}")
        else:
            print("\nAll schemes were selected at least once.")

        # count weightings distribution
        weighting_counts = Counter(
            result["selected_weighting"] for result in self.results
        )

        print("\nWeighting distribution:")
        print("-" * 40)
        print(f"{'Weighting':<15} | {'Count':<10} | {'Percentage':<10}")
        print("-" * 40)

        for weighting, count in weighting_counts.items():
            percentage = (count / len(self.results)) * 100
            print(f"{weighting:<15} | {count:<10} | {percentage:.2f}%")

        # save results to file
        self.save_results_to_json()

    def save_results_to_json(self):
        """save simulation results to a JSON file"""
        timestamp = int(time.time())
        filename = f"dKI_montecarlo_{self.num_trials}_{timestamp}.json"

        # count winning schemes
        scheme_counts = Counter(result["winning_scheme"] for result in self.results)
        scheme_percentages = {
            scheme: (count / len(self.results)) * 100
            for scheme, count in scheme_counts.items()
        }

        # count weightings
        weighting_counts = Counter(
            result["selected_weighting"] for result in self.results
        )
        weighting_percentages = {
            weighting: (count / len(self.results)) * 100
            for weighting, count in weighting_counts.items()
        }

        # prepare summary data
        summary_data = {
            "num_trials": self.num_trials,
            "valid_trials": len(self.results),
            "scheme_counts": {
                self.schemes[scheme]: count for scheme, count in scheme_counts.items()
            },
            "scheme_percentages": {
                self.schemes[scheme]: percentage
                for scheme, percentage in scheme_percentages.items()
            },
            "weighting_counts": dict(weighting_counts),
            "weighting_percentages": weighting_percentages,
            "never_selected": [
                self.schemes[scheme_id]
                for scheme_id in self.schemes
                if scheme_id not in scheme_counts
            ],
        }

        # write the summary data to a JSON file
        with open(filename, "w") as f:
            json.dump(summary_data, f, indent=4)

        print(f"\nDetailed simulation results saved to {filename}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Monte Carlo simulation for dKI assessment"
    )
    parser.add_argument(
        "--trials", type=int, default=1000, help="Number of simulation trials to run"
    )
    args = parser.parse_args()

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
        return 1

    print(f"Starting Monte Carlo simulation with {args.trials} trials...")
    simulation = DKIMonteCarloSimulation(num_trials=args.trials)
    simulation.run_simulation()

    return 0


if __name__ == "__main__":
    main()
