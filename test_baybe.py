from baybe import Campaign
from baybe.targets import NumericalTarget
from baybe.objectives import SingleTargetObjective
from baybe.parameters import CategoricalParameter, NumericalDiscreteParameter
from baybe.searchspace import SearchSpace
# What we want to maximize
target = NumericalTarget(name="Yield")
objective = SingleTargetObjective(target=target)
# The "knobs" we can turn
parameters = [
    CategoricalParameter(name="Granularity", values=["coarse", "medium", "fine"]),
    NumericalDiscreteParameter(name="Pressure", values=[1, 5, 10]),
]
searchspace = SearchSpace.from_product(parameters)
# Create the campaign
campaign = Campaign(searchspace, objective)
# Ask BayBE: "what should I try first?"
recommendations = campaign.recommend(batch_size=3)
print("BayBE suggests trying these experiments:")
print(recommendations)
# Simulate running the experiments and feed results back
recommendations["Yield"] = [88.0, 55.0, 62.0]
campaign.add_measurements(recommendations)
# Ask for the next round of suggestions
next_round = campaign.recommend(batch_size=3)
print("\\nAfter learning, BayBE now suggests:")
print(next_round)