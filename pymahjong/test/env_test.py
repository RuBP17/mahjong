import pymahjong as pm
import numpy as np
import platform
import warnings
import time

import env_mahjong
import pymahjong as mp
import numpy as np
from copy import deepcopy
from collections import defaultdict

EnvMahjong4 = env_mahjong.EnvMahjong4

np.set_printoptions(threshold=np.inf)

def col_name(col):
    if col < 6:
        return f'手牌{col}'
    elif col < 30:
        return f'副露Relative Player[{(col-6)//6}] col={(col-6)%6}'
    elif col < 70:
        return f'牌河Relative Player[{(col-30)//10}] col={(col-30)%10}'
    elif col < 80:
        return f'场{col-70}'
    elif col < 81:
        return f'最后'
    elif col < 93:
        return f'Action col={col-81}'
    elif col < 110:
        return f'Oracle Relative Player[{(col-87)//6}] col={(col-93)%6}'
    else:
        return f'???'

def encoding_test_by_random_play(num_games=100, verbose=2, error_pause=0):

    winds = ['east', 'south', 'west', 'north']

    obs_container = np.zeros([111, 34], dtype=np.int8)
    act_container = np.zeros([47], dtype=np.int8)

    env_test = EnvMahjong4()

    steps_taken = 0
    max_steps = 1000

    wrong_times = 0
    # -------------- Return vs. pretrained player -------------
    start_time = time.time()
    game = 0

    payoffs_array = []
    winning_counts = []
    deal_in_counts = []

    wrong_dimensions_count = defaultdict(int)

    wrong_dimensions_total = np.zeros([111])

    while game < num_games:

        oya = np.random.randint(0, 4)
        game_wind = winds[np.random.randint(0, 4)]
        env_test.reset(oya, game_wind)

        payoffs = np.zeros([4])
        rl_step = 0

        for tt in range(max_steps):

            curr_pid = env_test.get_curr_player_id()
            valid_actions = env_test.get_valid_actions(nhot=False)

            if len(valid_actions) == 1:
                env_test.t.make_selection(0)
            else:
                dq_action_mask = env_test.get_valid_actions(nhot=True).astype(np.int8)

                act_container.fill(0)
                pm.encode_action(env_test.t, curr_pid, act_container)
                ag_action_mask = act_container.copy()

                wrong_action_dimensions = np.argwhere(abs(ag_action_mask - dq_action_mask)).flatten()

                for dim in wrong_action_dimensions:
                    if dim != 41 and dim != 46:
                        print("------------------------------------------------------")
                        print("action wrong dim:", dim)
                        print("DQ:", dq_action_mask)
                        print("AG:", ag_action_mask)
                        print("current player river tiles:", env_test.river_tiles[0])
                        print("current player river tiles:", env_test.river_tiles[1])
                        print("current player river tiles:", env_test.river_tiles[2])
                        print("current player river tiles:", env_test.river_tiles[3])
                        print(env_test.t.players[0].to_string())
                        print(env_test.t.players[1].to_string())
                        print(env_test.t.players[2].to_string())
                        print(env_test.t.players[3].to_string())
                        print(env_test.t.get_phase())
                        print("------------------------------------------------------")

                rl_step += 1

                # --------------- Check state encoding !!!!!!!! ---------------

                dq_obs = np.concatenate([env_test.get_obs(curr_pid).astype(np.int8),
                                         env_test.get_oracle_obs(curr_pid).astype(np.int8)], axis=0)
                obs_container.fill(0)
                pm.encode_table(env_test.t, curr_pid, True, obs_container)
                ag_obs = deepcopy(obs_container)
                if True:
                    if np.any(dq_obs != ag_obs):
                        wrong_dimensions = np.argwhere(np.sum(abs(dq_obs - ag_obs), axis=1)).flatten()
                        for dim in wrong_dimensions:

                            if dim not in [34, 35, 36, 37, 38, 44, 45, 46, 47, 48, 54, 55, 56, 57, 58, 64, 65, 66,
                                           67, 68, 70, 71, 72, 73, 74, 75, 76, 77, 97, 103, 109, 11, 17, 23, 29, 89]:
                                wrong_dimensions_count[dim] += 1

                                if verbose and not(6 <= dim < 30):
                                    print("----game {}, step {}, player {}, dim {}, col: {} ----".format(
                                        game, rl_step, curr_pid, dim, col_name(dim)))
                                    print("tile index:   " , (np.linspace(0, 33, 34) % 9 + 1).astype(int))
                                    print("DQ's encoding:", dq_obs[dim, :])
                                    print("AG's encoding:", ag_obs[dim, :])

                                    # print("current player river tiles:", env_test.river_tiles[0])
                                    # print("current player river tiles:", env_test.river_tiles[1])
                                    # print("current player river tiles:", env_test.river_tiles[2])
                                    # print("current player river tiles:", env_test.river_tiles[3])
                                    print(env_test.t.players[0].to_string())
                                    print(env_test.t.players[1].to_string())
                                    print(env_test.t.players[2].to_string())
                                    print(env_test.t.players[3].to_string())
                                    print(env_test.t.get_phase())
                                    print("------------------------------------------------------")

                                    time.sleep(error_pause)

                        # if verbose >= 1:
                        #     print("wrong encoding! feature dimensions that are different: \n", wrong_dimensions)
                        # if verbose >= 2:
                        #     for dim in wrong_dimensions:
                        #         if dim not in [34, 35, 36, 37, 38, 44, 45, 46, 47, 48, 54, 55, 56, 57, 58, 64, 65, 66, 67, 68, 80, 82, 83, 84, 70, 71, 72, 73, 74, 75, 76, 77]:
                        #             print("-------step {}, player {}, col: {} ---------------".format(rl_step, curr_pid, col_name(dim)))
                        #             if 70 <= dim <= 77:
                        #                 print("DQ's encoding:", dq_obs[dim: dim + 4, :])
                        #                 print("AG's encoding:", ag_obs[dim: dim + 4, :])
                        #             else:
                        #                 print("DQ's encoding:", dq_obs[dim, :])
                        #                 print("AG's encoding:", ag_obs[dim, :])
                        #             print("------------------------------------------------------")
                        #
                        #             print("current player river tiles:", env_test.river_tiles[0])
                        #             print("current player river tiles:", env_test.river_tiles[1])
                        #             print("current player river tiles:", env_test.river_tiles[2])
                        #             print("current player river tiles:", env_test.river_tiles[3])
                        #             print(env_test.t.players[0].to_string())
                        #             print(env_test.t.players[1].to_string())
                        #             print(env_test.t.players[2].to_string())
                        #             print(env_test.t.players[3].to_string())
                        #             print(env_test.t.get_phase())
                        #
                        #             time.sleep(error_pause)
                        #             wrong_times += 1

                        # wrong_dimensions_total[np.argwhere(np.sum(abs(dq_obs - ag_obs), axis=1)).flatten()] = 1

                # --------------------------------------------------

                a = np.random.randint(0, len(valid_actions))
                sp, r, done, _ = env_test.step(curr_pid, valid_actions[a])
                steps_taken += 1

            if done or env_test.t.get_phase() == 16:

                payoffs = payoffs + np.array(env_test.get_payoffs())

                curr_wins = np.zeros([4])
                curr_deal_ins = np.zeros([4])

                if env_test.t.get_result().result_type == mp.ResultType.RonAgari:
                    for ii in range(4):  # consider multiple players Agari
                        if payoffs[ii] > 0:
                            curr_wins[ii] = 1
                    curr_deal_ins[np.argmin(payoffs)] = 1
                elif env_test.t.get_result().result_type == mp.ResultType.TsumoAgari:
                    curr_wins[np.argmax(payoffs)] = 1

                if game % 10 == 0:
                    print("game", game, payoffs)
                    print(wrong_dimensions_count)

                # results
                payoffs_array.append(payoffs)
                winning_counts.append(curr_wins)
                deal_in_counts.append(curr_deal_ins)
                game += 1
                break

    print("feature dimensions that are different \n:", np.argwhere(wrong_dimensions_total).flatten())
    print("Test {} games, spend {} s".format(num_games, time.time() - start_time))
    print("wrong times = ", wrong_times)


if __name__ == "__main__":

    # verbose = 0: only show feature dimensions that are different after playing all the games
    # verbose = 1: also show feature dimensions that are different at each step
    # verbose = 2: also show detailed data at the feature dimensions that are different at each step

    encoding_test_by_random_play(num_games=1000, verbose=1, error_pause=1)
