Convoluted
---
One-off branch difference visualizer for convoluted repositories with partially unrelated branches

---
Crawls through (two of) your repo branches and indicates whether each file:
 * exists in both branches with no differences - green
 * only exists in one of the branches - red
 * file differs between the branches - yellow

####Install
```bash
pip install -r requirements.txt
```
####Usage
```bash
./convoluted.py <branch1> <branch2> <repo path> > output.html
xdg-open output.html
# ...or use your favourite browser directly
```