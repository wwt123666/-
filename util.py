# usr/bin/env python
# -*- coding:utf-8- -*-

# 0 不加速
# 1 直接落地
JIASU = 0


#  对指定俄罗斯方块进行移动(不进行碰撞判断，不改变画板图像，只改变俄罗斯方块坐标)
def move_block(block, direction):
    c, r = block['cr']
    dc, dr = direction
    block['cr'] = [c + dc, r + dr]


#  对某个俄罗斯方块对象的cell_list变量进行对应角度更改
def get_cell_list_by_angle(cell_list, angle):
    angle_dict = {
        0: (1, 0, 0, 1),
        1: (0, 1, -1, 0),
        2: (-1, 0, 0, -1),
        3: (0, -1, 1, 0),
    }
    a, b, c, d = angle_dict[angle]
    if angle == 0:
        return cell_list

    rotate_cell_list = []
    for cell in cell_list:
        cc, cr = cell
        rc, rr = a * cc + b * cr, c * cc + d * cr
        rotate_cell_list.append((rc, rr))

    return rotate_cell_list


#  从参数俄罗斯方块中读取数据，进行AI计算，最佳坐标及最佳旋转角度，对俄罗斯方块cell_list对象进行更改，并在board列表中记录当前方块type
def save_block_to_list(block, board, isFuture=False):
    shape_type = block['kind']
    cc, cr = block['cr']
    cell_list = block['cell_list']

    if isFuture:
        cc, cr = block['best']['cr']
        angle = block['best']['angle']
        cell_list = get_cell_list_by_angle(cell_list, angle)

    for cell in cell_list:
        cell_c, cell_r = cell
        c = cell_c + cc
        r = cell_r + cr
        # 在board对应位置记下其类型
        board[r][c] = shape_type


#  检查当前行是否满块，返回值为布尔类型(函数参数为board中的列表对象)
def check_row_complete(row):
    for cell in row:
        if cell == '':
            return False

    return True


#  对俄罗斯方块能否移动进行判断，返回值为布尔类型
def check_move(board, cr, cell_list, direction):
    """

    :param board: block_list
    :param cr: 输入俄罗斯方块的坐标
    :param cell_list: 输入俄罗斯方块的cell_list
    :param direction: 移动方向
    :return:
    """
    board_r = len(board)
    board_c = len(board[0])
    cc, cr = cr
    cell_list = cell_list

    for cell in cell_list:
        cell_c, cell_r = cell
        c = cell_c + cc + direction[0]
        r = cell_r + cr + direction[1]
        # 判断该位置是否超出左右边界，以及下边界
        # 一般不判断上边界，因为俄罗斯方块生成的时候，可能有一部分在上边界之上还没有出来
        if c < 0 or c >= board_c or r >= board_r:
            return False

        # 必须要判断r不小于0才行，具体原因你可以不加这个判断，试试会出现什么效果
        if r >= 0 and board[r][c]:
            return False

    return True


#  判断俄罗斯方块在ci，ri位置上方是否有格挡方块,返回值为布尔类型
def check_above_empty(board, cell_list, ci, ri):
    for cell in cell_list:
        cc, cr = cell
        c, r = ci + cc, ri + cr
        for ir in range(r):
            if board[ir][c]:
                return False

    return True


#  对指定方块在对应列能满足插入的最下方的行ri进行查找并返回，并返回对应的列偏移量dc(在multi_tetris中调用)
def get_bottom_r(cell_list, board, ci):
    board_r = len(board)
    for ri in range(board_r - 1, -1, -1):
        if check_move(board, (ci, ri), cell_list, (0, 0)):
            for dc in [0, 1, -1]:
                nci = ci + dc
                if check_move(board, (nci, ri), cell_list, (0, 0)) and \
                        check_above_empty(board, cell_list, nci, ri):
                    return ri, dc

    raise Exception("no space to place")


#  对当前block_list进行权值运算
def cal_ai_score(block_list, board_c, board_r):  # board_c为总列数,board_r为总行数
    aggregate_height = 0  # 聚合高度
    holes = 0  # block_list中的空洞
    row_height_list = []  # 所有列的高度列表
    for ci in range(board_c):  # 在所有列中遍历
        find_first_cell = False  # 记录flag
        for ri in range(board_r):  # 在所有行中遍历
            if not find_first_cell and block_list[ri][ci]:  # 找到当前列最上方方格
                h = board_r - ri  # 当前列高度
                aggregate_height += h*h  # 聚合高度增加h
                row_height_list.append(h)  # 在列高列表增加h
                find_first_cell = True
            elif find_first_cell and not block_list[ri][ci]:
                holes += 1  # 空洞数量+1

        if not find_first_cell:
            row_height_list.append(0)  # 如果当前列没有方块，则将高度0添加至列表

    complete_lines = 0  # 完整行数量
    for row in block_list:
        if check_row_complete(row):
            complete_lines += 1

    bumpiness = 0  # 当前block_list颠簸值
    for ci in range(board_c - 1):  # x行则有x-1个颠簸值
        bumpiness += abs(row_height_list[ci] - row_height_list[ci + 1])  # 绝对值函数函数
    a = -2.10066
    b = 0.760666
    c = -0.35663
    d = -0.184483

    p = a * aggregate_height + b * complete_lines + c * holes + d * bumpiness
    return p


#  对当前俄罗斯方块到最佳位置的操作steps进行计算及存储(存储至block)
def cal_move_order(block):
    # 计算出移动到最佳位置的路径
    cc, cr = block['cr']  # 从俄罗斯方块中取出当前坐标
    best = block['best']  # 从俄罗斯方块中取出字典对象best
    bc, br = best['cr']  # 从best中取出最佳位置
    dc = best['dc']  # 从best中取出最佳位置的列偏移量
    bdc = bc + dc  # 目标列数
    angle_change_count = best['angle']  # 需要旋转的次数
    horizontal_move_count = abs(bdc - cc)  # 需要水平移动的次数

    speed = (angle_change_count + horizontal_move_count + 1) // br + 1  # 每下落一次移动次数

    steps = ['' for _ in range(br + 1)]  # steps为存储每一步操作的列表，多出一项用来存储最后一步的横向偏移

    for si in range(br):  # si为对应步数
        if angle_change_count >= speed:  # 如果一步(一个step字符串)存不下旋转俄罗斯方块操作
            steps[si] = 'W' * speed
            angle_change_count -= speed
        else:
            step = 'W' * angle_change_count  # 将剩余旋转操作存入step字符串中
            for i in range(speed - angle_change_count):  # step字符串剩余可存储位置
                if bdc < cc:
                    step += 'A'  # 进行横向移动标识存储
                    cc -= 1  # 改变列坐标
                elif bdc > cc:
                    step += 'D'  # 进行横向移动标识存储
                    cc += 1  # 改变列坐标
                else:
                    break

            angle_change_count = 0  # 清除旋转次数flag
            steps[si] = step  # 将step存储至steps列表

    if dc == 0:
        steps[br] = ''
    elif dc == 1:
        steps[br] = 'A'
    elif dc == -1:
        steps[br] = 'D'  # 将横向偏移数据存储至steps列表最后一项

    block['move_steps'] = steps


#  对方块进行移动操作，每调用一次该函数，修改一次block字典中cur_step和cr两项的值
def move_block_by_step(block):
    step_count = len(block['move_steps'])  # step_count读取move_steps长度
    si = block['cur_step']  # si存储当前步数，默认为0
    if si >= step_count:  # 对是否走完所有步进行判断
        return False

    step_str = block['move_steps'][si]  # 读取move_steps列表字符串
    c, r = block['cr']  # 读取原始坐标
    cell_list = block['cell_list']  # 读取cell_list

    if step_str == '' and JIASU == 1:
        if all(block['move_steps'][next_si] == '' for next_si in range(si, step_count)):
            si = step_count
            r = step_count - 1
            block['cur_step'] = si  # 改变flag的值
            block['cr'] = (c, r)  # 改变block行坐标至目标坐标上一行
            return True

    for step in step_str:  # 读取move_steps中的数据,对当行进行操作
        if step == 'A':
            c -= 1
        elif step == 'D':
            c += 1
        elif step == 'W':
            cell_list = get_cell_list_by_angle(cell_list, 1)

    if si == step_count - 1:  # 如果是最后一项，不改变行坐标，只改变列坐标
        pass
    else:
        r += 1
        # return False

    si += 1
    block['cur_step'] = si
    block['cr'] = (c, r)
    block['cell_list'] = cell_list
    return True


#  对board进行按行查找，找到满行则进行消去
def check_and_clear(board):  #
    score = 0  # score为分数
    board_r = len(board)  # 总行数
    board_c = len(board[0])  # 总列数
    for ri in range(board_r):
        if check_row_complete(board[ri]):
            # 当前行可消除
            if ri > 0:
                for cur_ri in range(ri, 0, -1):
                    board[cur_ri] = board[cur_ri - 1][:]
                board[0] = ['' for j in range(board_c)]
            else:
                board[ri] = ['' for j in range(board_c)]

            score += 10

    return score


#  另一个项目所需函数
def get_range(block_c, board_c, length):
    if block_c < length:
        return 0, min(board_c, 2 * length)
    elif block_c > board_c - length:
        return max(0, board_c - 2 * length), board_c
    else:
        return block_c - length, block_c + length
