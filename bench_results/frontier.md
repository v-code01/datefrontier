# datefrontier: how far ahead can a model count calendar days?

Ask 'What date is N days after D?' with the ground truth from Python's datetime.
Exact-date accuracy by the day span N, the frontier (largest N solved at >=0.5),
and how wrong the model is when wrong: the median absolute day error, the mean
signed error, and the fraction of errors within 5 days (approximately right).

## 1.5B (frontier 14 days)

  span   acc    median|err|  mean signed  approx(<=5d)  parse-fail
     1   0.82         1         +14      0.57         0.00
     3   0.80        10         +14      0.50         0.00
     7   0.90         2          +7      0.75         0.00
    14   0.60         2          +3      0.81         0.00
    30   0.25         4         +10      0.53         0.00
    60   0.05        12          +8      0.29         0.00
   100   0.03        28         -23      0.10         0.00
   365   0.03        94         +46      0.03         0.00

## 0.5B (frontier 1 days)

  span   acc    median|err|  mean signed  approx(<=5d)  parse-fail
     1   0.80         4          +6      0.62         0.00
     3   0.35         4          +6      0.73         0.00
     7   0.23        22         +22      0.40         0.03
    14   0.00        16         +22      0.08         0.03
    30   0.15        23         +70      0.47         0.00
    60   0.05        32         +85      0.18         0.00
   100   0.00       996       +1719      0.00         0.00
   365   0.03       335         +57      0.00         0.00

