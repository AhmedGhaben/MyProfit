@dataclass
class tradingEngine:

  """
  manages the trading operations:
  -opens/closes positions
  -runs the selected strategy

  this will be done using the broker's API (sending and receiving Protobuf messages)
  """