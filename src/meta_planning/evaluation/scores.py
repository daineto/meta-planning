class Score(object):
    def __init__(self, f1_score, precision_pres, recall_pres, precision_adds, recall_adds, precision_dels, recall_dels, avg_precision, avg_recall, matchings):
        self.f1_score = f1_score
        self.precision_pres = precision_pres
        self.recall_pres = recall_pres
        self.precision_adds = precision_adds
        self.recall_adds = recall_adds
        self.precision_dels = precision_dels
        self.recall_dels = recall_dels
        self.avg_precision = avg_precision
        self.avg_recall = avg_recall
        self.matchings = matchings

    def __str__(self):
        score_str = ""
        score_str += "F1 score: %s \n" % (self.f1_score)
        score_str += "PRE precision: %s, recall %s \n" % (self.precision_pres, self.recall_pres)
        score_str += "ADD precision: %s, recall %s \n" % (self.precision_adds, self.recall_adds)
        score_str += "DEL precision: %s, recall %s \n" % (self.precision_dels, self.recall_dels)
        score_str += "AVG precision: %s, recall %s \n" % (self.avg_precision, self.avg_recall)
        score_str += "Matchings: \n"
        for matching in self.matchings:
            score_str += "\t%s\n" % matching

        return score_str