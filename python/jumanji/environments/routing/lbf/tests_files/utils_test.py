# Copyright 2022 InstaDeep Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import chex
import jax
import jax.numpy as jnp

import jumanji.environments.routing.lbf.utils as utils
from jumanji.environments.routing.lbf.constants import DOWN, LEFT, LOAD, NOOP, RIGHT, UP
from jumanji.environments.routing.lbf.types import Agent, Food


def test_place_entities_on_grid(
    agent_grid: chex.Array, food_grid: chex.Array, food_items: Food, agents: Agent
) -> None:
    grid = jnp.zeros((6, 6), dtype=jnp.int32)

    agent_grid_result = jax.vmap(utils.place_agent_on_grid, (0, None))(agents, grid)
    agent_grid_result = jnp.sum(agent_grid_result, axis=0)
    assert jnp.all(jnp.allclose(agent_grid_result, agent_grid))

    food_grid_result = jax.vmap(utils.place_agent_on_grid, (0, None))(food_items, grid)
    food_grid_result = jnp.sum(food_grid_result, axis=0)
    assert jnp.all(jnp.allclose(food_grid_result, food_grid))


def test_simulate_agent_movement(
    agent0: Agent, agent1: Agent, agent2: Agent, agents: Agent, food_items: Food
) -> None:
    grid_size = 6
    agent0_new = utils.simulate_agent_movement(
        agent0, RIGHT, food_items, agents, grid_size
    )
    assert jnp.all(agent0_new.position == jnp.array([0, 1]))
    agent1_new = utils.simulate_agent_movement(
        agent1, LEFT, food_items, agents, grid_size
    )
    assert jnp.all(agent1_new.position == jnp.array([1, 0]))

    # Move agent out of bounds
    agent0_new = utils.simulate_agent_movement(
        agent0, UP, food_items, agents, grid_size
    )
    assert jnp.all(agent0_new.position == agent0.position)

    # Move agent1 to take the position of the food0
    agent1_new = utils.simulate_agent_movement(
        agent1, DOWN, food_items, agents, grid_size
    )
    assert jnp.all(agent1_new.position == agent1.position)

    # Try to load and do nothing.
    agent2_new = utils.simulate_agent_movement(
        agent2, NOOP, food_items, agents, grid_size
    )
    assert jnp.all(agent2_new.position == agent2.position)
    agent2_new = utils.simulate_agent_movement(
        agent2, LOAD, food_items, agents, grid_size
    )
    assert jnp.all(agent2_new.position == agent2.position)


def test_are_entities_adjacent(
    agents: Agent,
    agent0: Agent,
    agent1: Agent,
    agent2: Agent,
    food0: Food,
    food1: Food,
    food2: Food,
    food_items: Food,
) -> None:

    assert utils.are_entities_adjacent(agent1, food0)
    assert utils.are_entities_adjacent(agent2, food0)
    assert utils.are_entities_adjacent(agent2, food1)
    assert not utils.are_entities_adjacent(agent0, agent1)
    assert not utils.are_entities_adjacent(agent0, agent2)
    assert not utils.are_entities_adjacent(agent0, food0)
    assert not utils.are_entities_adjacent(agent1, agent2)
    assert not utils.are_entities_adjacent(agent2, food2)

    # check that vmap also works with are_entities_adjacent
    assert jnp.all(
        jax.vmap(utils.are_entities_adjacent, (0, None))(agents, agent0)
        == jnp.array([False, False, False])
    )
    assert jnp.all(
        jax.vmap(utils.are_entities_adjacent, (0, None))(agents, food0)
        == jnp.array([False, True, True])
    )
    assert jnp.all(
        jax.vmap(utils.are_entities_adjacent, (0, None))(food_items, agent2)
        == jnp.array([True, True, False])
    )

    assert jnp.all(
        jax.vmap(utils.are_entities_adjacent, (0, None))(food_items, food0)
        == jnp.array([False, False, False])
    )


def test_eat_food(agents: Agent, food0: Food, food1: Food, food2: Food) -> None:
    # food0 can be eaten by agent1 and agent2, food1 can be eaten by agent2.
    # set all agent actions to loading
    all_loading_agents = jax.vmap(lambda agent: agent.replace(loading=True))(agents)

    # check that food 0 can be eaten
    new_food0, eaten_food0, adj_agents = utils.eat_food(all_loading_agents, food0)
    assert new_food0.eaten == eaten_food0
    assert jnp.all(adj_agents == (agents.level * jnp.array([0, 1, 1])))

    # check that food 0 can be eaten
    new_food1, eaten_food1, adj_agents = utils.eat_food(all_loading_agents, food1)
    assert new_food1.eaten == eaten_food1
    assert jnp.all(adj_agents == (agents.level * jnp.array([0, 0, 1])))

    # check that food 2 cannot be eaten
    new_food2, eaten_food2, adj_agents = utils.eat_food(all_loading_agents, food2)
    assert [new_food2.eaten, eaten_food2] == [False, False]
    assert jnp.all(adj_agents == agents.level * jnp.array([0, 0, 0]))

    # check that if food is already eaten, it cannot be eaten again
    new_food0, eaten_food0, adj_agents = utils.eat_food(all_loading_agents, new_food0)
    assert new_food0.eaten != eaten_food0
    assert jnp.all(adj_agents == agents.level * jnp.array([0, 0, 0]))


def test_fix_collisions(agents: Agent) -> None:
    # agents original postions: [[0, 0], [0, 1], [1, 0], [1, 2]]

    # fake moves for agents:
    moved_agents = jax.vmap(Agent)(
        id=agents.id,
        level=agents.level,
        # collision on agent 0 and 3
        position=jnp.array([[0, 1], [0, 1], [2, 1]]),
        loading=jnp.array([0, 0, 0]),
    )

    # expected postions after collision fix:
    expected_agents = jax.vmap(Agent)(
        id=agents.id,
        level=agents.level,
        # take orig agent for agent 0 and 3
        position=jnp.array([[0, 0], [1, 1], [2, 1]]),
        loading=jnp.array([0, 0, 0]),
    )

    new_agents = utils.fix_collisions(moved_agents, agents)
    chex.assert_trees_all_equal(new_agents, expected_agents)


def test_slice_around() -> None:
    pos = jnp.array([1, 1])
    fov = 1

    grid = jnp.arange(9).reshape(3, 3)
    grid = jnp.pad(grid, 1, mode="constant", constant_values=-1)

    # expected slice
    expected_slice = jnp.array(
        [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
        ]
    )

    # slice around pos
    slice_coords = utils.slice_around(pos, fov)
    view = jax.lax.dynamic_slice(grid, slice_coords, (2 * fov + 1, 2 * fov + 1))

    assert jnp.all(view == expected_slice)

    # slice around pos with fov=2
    fov = 2
    expected_slice = jnp.array(
        [
            [-1, -1, -1, -1, -1],
            [-1, 0, 1, 2, -1],
            [-1, 3, 4, 5, -1],
            [-1, 6, 7, 8, -1],
            [-1, -1, -1, -1, -1],
        ]
    )

    slice_coords = utils.slice_around(pos, fov)
    view = jax.lax.dynamic_slice(grid, slice_coords, (2 * fov + 1, 2 * fov + 1))
    assert jnp.all(view == expected_slice)


def test_calculate_num_observation_features() -> None:
    num_food = 4
    num_agents = 6
    obs_features = jnp.array(3 * (num_agents + num_food), jnp.int32)
    calculated_obs_features = utils.calculate_num_observation_features(
        num_food=num_food, num_agents=num_agents
    )
    assert jnp.all(calculated_obs_features == obs_features)
