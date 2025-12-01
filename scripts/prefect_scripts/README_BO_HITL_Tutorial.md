# Bayesian Optimization Human-in-the-Loop Slack Integration Tutorial

Demonstrates a BO campaign with human evaluation via Slack and Prefect.

## Workflow

1. **Run script** - starts BO campaign via Ax Service API
2. **Ax suggests parameters** - sends Slack notification with x1, x2 values
3. **User evaluates** - uses HuggingFace Branin space
4. **User resumes** - enters objective value in Prefect UI via Slack link
5. **Loop continues** - 5 iterations to find optimal parameters

## Setup

### 1. Install Dependencies

```bash
pip install ax-platform prefect prefect-slack pymongo
```

### 2. Start Prefect Server

```bash
prefect server start
```

### 3. Configure Slack Webhook Block

```python
from prefect.blocks.notifications import SlackWebhook

slack_webhook_block = SlackWebhook(url="YOUR_SLACK_WEBHOOK_URL")
slack_webhook_block.save("prefect-test")
```

Get webhook URL from https://api.slack.com/apps

### 4. Configure MongoDB (Optional)

Set environment variable for experiment storage:
```bash
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/"
```

### 5. Run

```bash
python bo_hitl_slack_tutorial.py
```

## Files

- `bo_hitl_slack_tutorial.py` - Main tutorial (single file implementation)
- `requirements.txt` - Dependencies

## Demo Video

Show:
1. Running script
2. Receiving Slack notification
3. Evaluating on HuggingFace Branin space
4. Clicking Slack link to Prefect UI
5. Entering objective value
6. Repeat 4-5 times

## References

- [Ax Documentation](https://ax.dev/)
- [Prefect Interactive Workflows](https://docs.prefect.io/latest/guides/creating-interactive-workflows/)
- [HuggingFace Branin Space](https://huggingface.co/spaces/AccelerationConsortium/branin)
