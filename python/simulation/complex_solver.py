from astar import find_path
import math

class ComplexSolver:
  def __init__(self, environment):
    # The environment to make decisions for
    self.environment = environment

    # The targets for each bot to move towards. The index is None if there is no curent target (will find one in the next step)
    self.targets = [{
      'type': 'apple',
      'index': None
    } for _ in range(len(self.environment.bots))]

    # The rough paths for each bot to follow. These are the paths that the bots will follow to reach their targets
    # provided by the A* algorithm. The paths are recalculated every time the bot gets a new target
    # or the path becomes invalid.
    self.rough_paths: list[tuple[float, float]] = [None] * len(self.environment.bots)
  
  def make_decisions(self):
    """
    Makes a decision for each bot based on the current environment,
    then executes those decisions and returns the new state of the environment.
    """

    decisions = ['idle'] * len(self.environment.bots)

    for bot_index in range(len(self.environment.bots)):
      decisions[bot_index] = self.__make_decision(bot_index)

    print(decisions)

    self.environment.step(decisions)

    return self.environment

  def __make_decision(self, bot_index: int) -> str:
    """
    Makes a decision for a single bot based on the current environment.

    :param bot_index: The index of the bot to make a decision for.

    :return: [str] the action to take.
    """
    # If all apples have been collected, do nothing
    if len([apple for apple in self.environment.apples if not apple['collected']]) == 0:
      return 'idle'
    
    bot = self.environment.bots[bot_index]
    
    # If the bot is next to an apple, pick it up
    if bot['holding'] is None and self.environment.try_pick(bot_index) is not None:
      self.rough_paths[bot_index] = None
      self.targets[bot_index] = {
        'type': 'basket',
        'index': None
      }
      return 'pick'

    # If the bot is holding an apple next to a basket, drop it
    if bot['holding'] is not None and self.environment.can_drop(bot_index) is not None:
      self.rough_paths[bot_index] = None
      self.targets[bot_index] = {
        'type': 'apple',
        'index': None
      }
      return 'drop'
    
    # If the bot already has a target, move towards it
    if self.targets[bot_index]['index'] is not None:
      return self.__move_towards_target(bot_index, self.targets[bot_index])
    
    # Otherwise, find a new target
    new_target = self.__find_target(bot_index)

    # If there aren't any valid targets to move towards, do nothing
    if new_target is None:
      return 'idle'
    
    self.targets[bot_index] = new_target
    return self.__move_towards_target(bot_index, new_target)

  def __find_target(self, bot_idx: int) -> dict:
    """
    Finds a target for a bot to move towards.

    :param bot_idx: The index of the bot to find a target for.

    :return: [dict] the target for the bot to move towards.
    """
    empty_hands = self.environment.bots[bot_idx]['holding'] is None
    targets = self.environment.apples if empty_hands else self.environment.baskets
    valid_targets = [i for i, target in enumerate(targets) if not target['collected'] and not target['held']]

    if len(valid_targets) == 0:
      return None
    
    target_idx = min(valid_targets, key=lambda target_idx: self.environment.distance(
      targets[target_idx]['x'],
      targets[target_idx]['y'],
      self.environment.bots[bot_idx]['x'],
      self.environment.bots[bot_idx]['y']
    ))

    return {
      'type': 'apple' if empty_hands else 'basket',
      'index': target_idx
    }

  def __move_towards_target(self, bot_idx: int, target: dict) -> str:
    """
    Moves the bot towards the target.

    :param bot_idx: The index of the bot to move.
    :param target: The target to move towards.

    :return: [str] the action to take.
    """
    goal = self.__get_goal_coords(bot_idx, target)
    print(goal)
    print((self.environment.bots[bot_idx]['x'], self.environment.bots[bot_idx]['y']))

    nose_x, nose_y = self.__get_nose(bot_idx)
    print((nose_x, nose_y))

    # Find the angle from the bot to the goal [0, 2pi]
    goal_angle = (math.atan2(goal[1] - self.environment.bots[bot_idx]['y'], goal[0] - self.environment.bots[bot_idx]['x']) + 2 * math.pi) % (2 * math.pi)

    # Find the delta between the bot's orientation and the goal angle
    current_angle = self.angle_difference(self.environment.bots[bot_idx]['orientation'], goal_angle)

    # Find the delta between the bot's orientation and the goal angle if it turned left or right
    left_angle = self.angle_difference(self.environment.bots[bot_idx]['orientation'] - self.environment.ROBOT_TURN_SPEED, goal_angle)
    right_angle = self.angle_difference(self.environment.bots[bot_idx]['orientation'] + self.environment.ROBOT_TURN_SPEED, goal_angle)

    if abs(left_angle) < abs(current_angle):
      return 'left'
    
    if abs(right_angle) < abs(current_angle):
      return 'right'
    
    # Then check if moving forward or backwards would help
    forward_dist = self.environment.distance(
      nose_x + math.cos(self.environment.bots[bot_idx]['orientation']) * self.environment.ROBOT_MOVE_SPEED,
      nose_y + math.sin(self.environment.bots[bot_idx]['orientation']) * self.environment.ROBOT_MOVE_SPEED,
      goal[0],
      goal[1]
    )

    backward_dist = self.environment.distance(
      nose_x - math.cos(self.environment.bots[bot_idx]['orientation']) * self.environment.ROBOT_MOVE_SPEED,
      nose_y - math.sin(self.environment.bots[bot_idx]['orientation']) * self.environment.ROBOT_MOVE_SPEED,
      goal[0],
      goal[1]
    )

    if forward_dist < backward_dist:
      return 'forward'
    
    return 'backward'

  def __get_goal_coords(self, bot_idx: int, target: dict) -> tuple[float, float]:
    """
    Find the coordinates of the goal for the bot to move towards.

    :param bot_idx: The index of the bot to move.
    :param target: The target to move towards.

    :return: [tuple[float, float]] the coordinates of the goal.
    """
    if self.rough_paths[bot_idx] is None:
      self.rough_paths[bot_idx] = self.__astar_grid_safe(bot_idx, target)
      if self.rough_paths[bot_idx] is None:
        self.rough_paths[bot_idx] = []

    print(self.rough_paths[bot_idx])
    
    # Check to see if the bot has arrived at the first point in the path
    if len(self.rough_paths[bot_idx]) > 0:
      nose = self.__get_nose(bot_idx)

      # If the bot is within 2 steps of the next point in the path, go to the next point
      while len(self.rough_paths[bot_idx]) > 0 and self.environment.distance(nose[0], nose[1], self.rough_paths[bot_idx][0][0], self.rough_paths[bot_idx][0][1]) < self.environment.ROBOT_MOVE_SPEED * 2:
        self.rough_paths[bot_idx].pop(0)

    # Find the actual coordiantes where the bot should be moving towards
    target_object = self.environment.apples[target['index']] if target['type'] == 'apple' else self.environment.baskets[target['index']]

    if len(self.rough_paths[bot_idx]) == 0:
      return target_object['x'], target_object['y']
    
    return self.rough_paths[bot_idx][0]

  def __astar_grid_safe(self, bot_idx: int, target: dict) -> list[tuple[int, int]]:
    """
    Runs the A* algorithm with multiple scales to find a path for the bot to follow.

    :param bot_idx: The index of the bot to move.
    :param target: The target to move towards.

    :return: [list[tuple[int, int]]] the path to follow.
    """

    for scale in [10, 5, 2]:
      print(f'Running A* with scale {scale}')
      path = self.__astar_grid(bot_idx, target, scale)
      if path is not None:
        return path
      
    return None

  def __astar_grid(self, bot_idx: int, target: dict, scale: int) -> list[tuple[int, int]]:
    """
    Uses A* algorithm to generate a list of coordiates defining a path for the bot to follow.

    :param bot_idx: The index of the bot to move.
    :param target: The target to move towards.
    :param scale: The scale of the grid to use for pathfinding.
    The higher the number the less accurate the path will be but the faster it will be calculated.

    :return: [list[tuple[int, int]]] the path to follow
    """
    target_object = self.environment.apples[target['index']] if target['type'] == 'apple' else self.environment.baskets[target['index']]
    goal = (int(target_object['x'] / scale), int(target_object['y'] / scale))
    grid = self.__create_astar_grid(bot_idx, scale)

    print(grid)
    print(goal)

    def find_neighbors(loc):
      # To avoid the basket collision interfering with the pathfinding,
      # If the bot is within 20% of the goal radius, it is at the goal
      if math.hypot(goal[0] - loc[0], goal[1] - loc[1]) < target_object['diameter'] / 2 * 1.2:
        return [goal]

      neighbors = [(loc[0] + d[0], loc[1] + d[1]) for d in [(1, 0), (-1, 0), (0, 1), (0, -1)]]
      return [
        n
        for n in neighbors
        if grid[n[0]][n[1]]
      ]
    
    nose = self.__get_nose(bot_idx)

    print((int(nose[0] / scale), int(nose[1] / scale)))

    path = find_path(
      (int(nose[0] / scale), int(nose[1] / scale)),
      goal,
      neighbors_fnct=find_neighbors,
      distance_between_fnct=lambda loc1, loc2: abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])
    )

    if path is None:
      return None

    # Only return half of the path to avoid the bot getting stuck
    return [(p[0] * scale, p[1] * scale) for i, p in enumerate(path) if i % 2 == 0]
  
  def __create_astar_grid(self, bot_idx: int, scale: int) -> list[list[bool]]:
    """
    Creates a grid for the A* algorithm to use.

    :param bot_idx: The index of the bot to move.
    :param scale: The scale of the grid to use.

    :return: [list[list[bool]]] the grid to use.
    """
    grid = [[True] * (self.environment.height // scale) for _ in range(self.environment.width // scale)]

    def scale_num(num):
      return int(num / scale)

    for tree in self.environment.trees:
      for x in range(scale_num(tree['x'] - tree['diameter'] / 2) - 1, scale_num(tree['x'] + tree['diameter'] / 2) + 2):
        for y in range(scale_num(tree['y'] - tree['diameter'] / 2) - 1, scale_num(tree['y'] + tree['diameter'] / 2) + 2):
          grid[x][y] = self.environment.is_valid_location(x * scale, y * scale, self.environment.ROBOT_DIAMETER, bot_idx)

    for basket in self.environment.baskets:
      for x in range(scale_num(basket['x'] - basket['diameter'] / 2) - 1, scale_num(basket['x'] + basket['diameter'] / 2) + 2):
        for y in range(scale_num(basket['y'] - basket['diameter'] / 2) - 1, scale_num(basket['y'] + basket['diameter'] / 2) + 2):
          grid[x][y] = self.environment.is_valid_location(x * scale, y * scale, self.environment.ROBOT_DIAMETER, bot_idx)

    return grid
  
  def __get_nose(self, bot_idx: int) -> tuple[int, int]:
    """
    Returns the location of the bot's nose.

    :param bot_idx: The index of the bot to get the nose location of.

    :return: [tuple[int, int]] the location of the bot's nose.
    """
    bot = self.environment.bots[bot_idx]
    return (
      bot['x'] + math.cos(bot['orientation']) * bot['diameter'] / 2,
      bot['y'] + math.sin(bot['orientation']) * bot['diameter'] / 2
    )
  
  @staticmethod
  def angle_difference(angle1: float, angle2: float) -> float:
    """
    Calculates the difference between two angles.

    :param: angle1 [float] The first angle.
    :param: angle2 [float] The second angle.

    :return: [float] The difference between the two angles.
    """

    higher = max(angle1, angle2)
    lower = min(angle1, angle2)

    if higher - lower > math.pi:
      return 2 * math.pi - higher + lower
    
    return higher - lower