import dedupe
from collections import defaultdict
import unittest

from future.utils import viewitems, viewvalues

class BlockingTest(unittest.TestCase):
  def setUp(self):
    self.frozendict = dedupe.core.frozendict

    field_definition = [{'field' : 'name', 'type': 'String'}, 
                        {'field' :'age', 'type': 'String'}]
    self.data_model = dedupe.Dedupe(field_definition).data_model
    self.training_pairs = {
        0: [((1, self.frozendict({"name": "Bob", "age": "50"})),
             (2, self.frozendict({"name": "Bob", "age": "75"}))),
            ((3, self.frozendict({"name": "Meredith", "age": "40"})),
             (4, self.frozendict({"name": "Sue", "age": "10"})))], 
        1: [((5, self.frozendict({"name": "Jimmy", "age": "20"})),
             (6, self.frozendict({"name": "Jimbo", "age": "21"}))),
            ((7, self.frozendict({"name": "Willy", "age": "35"})),
             (8, self.frozendict({"name": "William", "age": "35"}))),
            ((9, self.frozendict({"name": "William", "age": "36"})),
             (8, self.frozendict({"name": "William", "age": "35"})))]
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

  def test_dedupe_coverage(self) :
    predicates = self.data_model['fields'][0].predicates
    coverage = dedupe.training.DedupeCoverage(predicates, self.training)
    assert self.simple(coverage.overlap.keys()).issuperset(
          set(["SimplePredicate: (tokenFieldPredicate, name)", 
               "SimplePredicate: (commonSixGram, name)", 
               "TfidfTextSearchPredicate: (0.4, name)", 
               "SimplePredicate: (sortedAcronym, name)",
               "SimplePredicate: (sameThreeCharStartPredicate, name)", 
               "TfidfTextSearchPredicate: (0.2, name)", 
               "SimplePredicate: (sameFiveCharStartPredicate, name)", 
               "TfidfTextSearchPredicate: (0.6, name)", 
               "SimplePredicate: (wholeFieldPredicate, name)", 
               "TfidfTextSearchPredicate: (0.8, name)", 
               "SimplePredicate: (commonFourGram, name)", 
               "SimplePredicate: (firstTokenPredicate, name)", 
               "SimplePredicate: (sameSevenCharStartPredicate, name)"]))

    overlap = coverage.predicateCoverage(predicates, self.distinct_ids)
    assert set(str(k) for k in overlap.keys()).issuperset(
          set(["TfidfTextSearchPredicate: (0.4, name)", 
               "TfidfTextSearchPredicate: (0.6, name)", 
               "SimplePredicate: (sortedAcronym, name)",
               "SimplePredicate: (wholeFieldPredicate, name)", 
               "SimplePredicate: (sameThreeCharStartPredicate, name)",
               "SimplePredicate: (tokenFieldPredicate, name)", 
               "TfidfTextSearchPredicate: (0.8, name)", 
               "SimplePredicate: (firstTokenPredicate, name)", 
               "TfidfTextSearchPredicate: (0.2, name)"]))

    overlap = coverage.predicateCoverage(predicates, self.dupe_ids)
    assert set(str(k) for k in overlap.keys()).issuperset(
          set(["SimplePredicate: (tokenFieldPredicate, name)", 
               "SimplePredicate: (commonSixGram, name)", 
               "TfidfTextSearchPredicate: (0.4, name)", 
               "SimplePredicate: (sortedAcronym, name)",
               "SimplePredicate: (sameThreeCharStartPredicate, name)", 
               "TfidfTextSearchPredicate: (0.2, name)", 
               "SimplePredicate: (sameFiveCharStartPredicate, name)", 
               "TfidfTextSearchPredicate: (0.6, name)", 
               "SimplePredicate: (wholeFieldPredicate, name)", 
               "TfidfTextSearchPredicate: (0.8, name)", 
               "SimplePredicate: (firstTokenPredicate, name)", 
               "SimplePredicate: (commonFourGram, name)", 
               "SimplePredicate: (sameSevenCharStartPredicate, name)"]))

    predicates = self.data_model['fields'][0].predicates

    coverage = dedupe.training.RecordLinkCoverage(predicates, self.training)
    assert self.simple(coverage.overlap.keys()).issuperset(
          set(["SimplePredicate: (tokenFieldPredicate, name)", 
               "SimplePredicate: (commonSixGram, name)", 
               "TfidfTextSearchPredicate: (0.4, name)", 
               "SimplePredicate: (sameThreeCharStartPredicate, name)", 
               "TfidfTextSearchPredicate: (0.2, name)", 
               "SimplePredicate: (sameFiveCharStartPredicate, name)", 
               "TfidfTextSearchPredicate: (0.6, name)", 
               "SimplePredicate: (firstTokenPredicate, name)", 
               "SimplePredicate: (wholeFieldPredicate, name)", 
               "TfidfTextSearchPredicate: (0.8, name)", 
               "SimplePredicate: (sortedAcronym, name)",
               "SimplePredicate: (commonFourGram, name)", 
               "SimplePredicate: (sameSevenCharStartPredicate, name)"]))


    
class TfidfTest(unittest.TestCase):
  def setUp(self):
    self.data_d = {
                     100 : {"name": "Bob", "age": "50", "dataset": 0},
                     105 : {"name": "Charlie", "age": "75", "dataset": 1},
                     110 : {"name": "Meredith", "age": "40", "dataset": 1},
                     115 : {"name": "Sue", "age": "10", "dataset": 0},
                     120 : {"name": "Jimbo", "age": "21","dataset": 0},
                     125 : {"name": "Jimbo", "age": "21", "dataset": 0},
                     130 : {"name": "Willy", "age": "35", "dataset": 0},
                     135 : {"name": "Willy", "age": "35", "dataset": 1},
                     140 : {"name": "Martha", "age": "19", "dataset": 1},
                     145 : {"name": "Kyle", "age": "27", "dataset": 0},
                  }
    

  def test_unconstrained_inverted_index(self):

    blocker = dedupe.blocking.Blocker([dedupe.predicates.TfidfTextSearchPredicate(0.0, "name")])

    blocker.index(set(record["name"] 
                           for record 
                           in viewvalues(self.data_d)),
                       "name")

    blocks = defaultdict(set)
    
    for block_key, record_id in blocker(self.data_d.items()) :
      blocks[block_key].add(record_id)

    blocks = set([frozenset(block) for block in blocks.values()
                  if len(block) > 1 ])

    assert blocks ==\
        set([frozenset([120, 125]), frozenset([130, 135])])

class TfIndexUnindex(unittest.TestCase) :
  def setUp(self) :
    data_d = {
      100 : {"name": "Bob", "age": "50", "dataset": 0},
      105 : {"name": "Charlie", "age": "75", "dataset": 1},
      110 : {"name": "Meredith", "age": "40", "dataset": 1},
      115 : {"name": "Sue", "age": "10", "dataset": 0},
      120 : {"name": "Jimbo", "age": "21","dataset": 0},
      125 : {"name": "Jimbo", "age": "21", "dataset": 0},
      130 : {"name": "Willy", "age": "35", "dataset": 0},
      135 : {"name": "Willy", "age": "35", "dataset": 1},
      140 : {"name": "Martha", "age": "19", "dataset": 1},
      145 : {"name": "Kyle", "age": "27", "dataset": 0},
    }


    self.blocker = dedupe.blocking.Blocker([dedupe.predicates.TfidfTextSearchPredicate(0.0, "name")])

    self.records_1 = dict((record_id, record) 
                          for record_id, record 
                          in viewitems(data_d)
                          if record["dataset"] == 0)

    self.fields_2 = dict((record_id, record["name"])
                         for record_id, record 
                         in viewitems(data_d)
                         if record["dataset"] == 1)


  def test_index(self):
    self.blocker.index(set(self.fields_2.values()), "name")

    blocks = defaultdict(set)
    
    for block_key, record_id in self.blocker(self.records_1.items()) :
      blocks[block_key].add(record_id)

    assert list(blocks.items())[0][1] == set([130])


  def test_doubled_index(self):
    self.blocker.index(self.fields_2.values(), "name")
    self.blocker.index(self.fields_2.values(), "name")

    blocks = defaultdict(set)
    
    for block_key, record_id in self.blocker(self.records_1.items()) :
      blocks[block_key].add(record_id)

    assert list(blocks.items()) == [(u'4:0', set([130]))]

  def test_unindex(self) :
    self.blocker.index(self.fields_2.values(), "name")
    self.blocker.unindex(self.fields_2.values(), "name")

    blocks = defaultdict(set)
    
    for block_key, record_id in self.blocker(self.records_1.items()) :
      blocks[block_key].add(record_id)

    assert len(blocks.values()) == 0 






    

if __name__ == "__main__":
    unittest.main()
