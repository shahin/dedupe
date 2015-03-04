import dedupe
from collections import defaultdict
import unittest

class ConstrainedBlockingTest(unittest.TestCase):
  def setUp(self):
    self.frozendict = dedupe.core.frozendict

    field_definition = [{'field' : 'name', 'type': 'String'}, 
                        {'field' : 'city', 'type': 'String'},
                        {'field' : 'age', 'type': 'String'}]
    self.data_model = dedupe.Dedupe(field_definition).data_model
    self.training_pairs = {
        0: [((1, self.frozendict({"name": "Bob", "age": "50", "city": "Chicago"})),
             (2, self.frozendict({"name": "Bob", "age": "75", "city": "San Francisco"}))),
            ((3, self.frozendict({"name": "Meredith", "age": "40", "city": "Chicago"})),
             (4, self.frozendict({"name": "Sue", "age": "10", "city": "San Francisco"})))], 
        1: [((5, self.frozendict({"name": "Jimmy", "age": "20", "city": "Chicago"})),
             (6, self.frozendict({"name": "Jimbo", "age": "21", "city": "Chicago"}))),
            ((7, self.frozendict({"name": "Willy", "age": "35", "city": "Chicago"})),
             (8, self.frozendict({"name": "William", "age": "35", "city": "Chicago"}))),
            ((9, self.frozendict({"name": "William", "age": "36", "city": "Chicago"})),
             (8, self.frozendict({"name": "William", "age": "35", "city": "Chicago"})))]
      }

    self.training = self.training_pairs[0] + self.training_pairs[1]
    self.distinct_ids = [tuple([pair[0][0], pair[1][0]])
                         for pair in
                         self.training_pairs[0]]
    self.dupe_ids = [tuple([pair[0][0], pair[1][0]])
                     for pair in
                     self.training_pairs[1]]

    self.simple = lambda x : set([str(k) for k in x 
                                  if "CompoundPredicate" not in str(k)])

  def test_banned_predicates(self) :
    predicates = self.data_model['fields'][0].predicates + self.data_model['fields'][1].predicates

    ConsrainedPredicatesDedupeCoverage = type(
        'ConsrainedPredicatesDedupeCoverage',
        (dedupe.training.CustomPredicateConstraints, dedupe.training.RecordLinkCoverage, object),
        {})

    coverage_banned_city = ConsrainedPredicatesDedupeCoverage(predicates, self.training, {'banned': ['city']})
    coverage = ConsrainedPredicatesDedupeCoverage(predicates, self.training)

    banned_predicates = set(coverage.overlap.keys()) - set(coverage_banned_city.overlap.keys())
    assert banned_predicates != set([])

    # make sure all removed simple predicates are for city
    banned_simple_predicate_fields = set([
        predicate.field
        for full_predicate in list(banned_predicates)
        for predicate in full_predicate
        if 'CompoundPredicate' not in str(full_predicate)])
    assert banned_simple_predicate_fields == set(['city'])

    # make sure all removed compound predicates include a predicate on city
    banned_compound_predicates = [
        full_predicate
        for full_predicate in list(banned_predicates)
        if 'CompoundPredicate' in str(full_predicate)]
    assert all(['city' in [predicate.field for predicate in full_predicate] for full_predicate in banned_compound_predicates])

    assert set(coverage.overlap.keys()).issuperset(coverage_banned_city.overlap.keys())

  def test_required_predicates(self):
    predicates = self.data_model['fields'][0].predicates + self.data_model['fields'][1].predicates

    ConsrainedPredicatesDedupeCoverage = type(
        'ConsrainedPredicatesDedupeCoverage',
        (dedupe.training.CustomPredicateConstraints, dedupe.training.RecordLinkCoverage, object),
        {})

    coverage_required_city = ConsrainedPredicatesDedupeCoverage(predicates, self.training, {'required': ['city']})
    coverage = ConsrainedPredicatesDedupeCoverage(predicates, self.training)

    insufficient_predicates = set(coverage.overlap.keys()) - set(coverage_required_city.overlap.keys())
    assert insufficient_predicates != set([])

    # make sure all removed simple predicates are for fields other than city 
    insufficient_simple_predicate_fields = set([
        predicate.field
        for full_predicate in list(insufficient_predicates)
        for predicate in full_predicate
        if 'CompoundPredicate' not in str(full_predicate)])
    assert insufficient_simple_predicate_fields & set(['city']) == set([])

    # make sure all removed compound predicates do not include a predicate on city
    insufficient_compound_predicates = [
        full_predicate
        for full_predicate in list(insufficient_predicates)
        if 'CompoundPredicate' in str(full_predicate)]
    assert all(['city' not in [predicate.field for predicate in full_predicate] for full_predicate in insufficient_compound_predicates])

    assert set(coverage.overlap.keys()).issuperset(coverage_required_city.overlap.keys())


if __name__ == "__main__":
    unittest.main()
