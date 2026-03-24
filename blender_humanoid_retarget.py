bl_info = {
    "name": "Humanoid Retarget (Godot Compatible)",
    "author": "D3ZAX",
    "version": (1,0,0),
    "blender": (4,5,0),
    "location": "View3D > Sidebar > Humanoid",
    "category": "Animation"
}

import bpy
import json
import mathutils
import re
import os
import difflib
from bpy.props import *
from bpy.types import Panel, Operator, PropertyGroup, UIList
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper
from mathutils import Vector, Matrix, Quaternion


# ---------------------------------------------------------
# Godot Humanoid bones
# ---------------------------------------------------------

HUMANOID_BONES = [

"Hips",

"Spine",
"Chest",
"UpperChest",
"Neck",
"Head",

"LeftEye",
"RightEye",
"Jaw",

"LeftShoulder",
"LeftUpperArm",
"LeftLowerArm",
"LeftHand",

"RightShoulder",
"RightUpperArm",
"RightLowerArm",
"RightHand",

"LeftUpperLeg",
"LeftLowerLeg",
"LeftFoot",
"LeftToes",

"RightUpperLeg",
"RightLowerLeg",
"RightFoot",
"RightToes",

# Left Fingers
"LeftThumbMetacarpal",
"LeftThumbProximal",
"LeftThumbDistal",

"LeftIndexProximal",
"LeftIndexIntermediate",
"LeftIndexDistal",

"LeftMiddleProximal",
"LeftMiddleIntermediate",
"LeftMiddleDistal",

"LeftRingProximal",
"LeftRingIntermediate",
"LeftRingDistal",

"LeftLittleProximal",
"LeftLittleIntermediate",
"LeftLittleDistal",

# Right Fingers
"RightThumbMetacarpal",
"RightThumbProximal",
"RightThumbDistal",

"RightIndexProximal",
"RightIndexIntermediate",
"RightIndexDistal",

"RightMiddleProximal",
"RightMiddleIntermediate",
"RightMiddleDistal",

"RightRingProximal",
"RightRingIntermediate",
"RightRingDistal",

"RightLittleProximal",
"RightLittleIntermediate",
"RightLittleDistal",

]

GODOT_BONEMAP = {

"Hips": [
    "hips","pelvis","root","hip","mixamorig:hips"
],

"Spine":[
    "spine","spine1","spine_01","spine01","abdomenupper"
],

"Chest":[
    "spine2","spine_02","spine02","chest","chestLower"
],

"UpperChest":[
    "spine3","spine_03","upperchest","chest2","chestUpper"
],

"Neck":[
    "neck","neck1"
],

"Head":[
    "head","skull"
],

# shoulders

"LeftShoulder":[
    "clavicle_l","l_clavicle","leftshoulder","shoulder_l"
],

"RightShoulder":[
    "clavicle_r","r_clavicle","rightshoulder","shoulder_r"
],

# arms

"LeftUpperArm":[
    "upperarm_l","arm_l","l_arm","leftarm"
],

"LeftLowerArm":[
    "forearm_l","lowerarm_l","l_forearm"
],

"LeftHand":[
    "hand_l","l_hand","lefthand"
],

"RightUpperArm":[
    "upperarm_r","arm_r","r_arm","rightarm"
],

"RightLowerArm":[
    "forearm_r","lowerarm_r","r_forearm"
],

"RightHand":[
    "hand_r","r_hand","righthand"
],

# legs

"LeftUpperLeg":[
    "thigh_l","upperleg_l","l_thigh"
],

"LeftLowerLeg":[
    "calf_l","lowerleg_l","l_calf"
],

"LeftFoot":[
    "foot_l","l_foot"
],

"LeftToes":[
    "toe_l","toes_l","l_toe"
],

"RightUpperLeg":[
    "thigh_r","upperleg_r","r_thigh"
],

"RightLowerLeg":[
    "calf_r","lowerleg_r","r_calf"
],

"RightFoot":[
    "foot_r","r_foot"
],

"RightToes":[
    "toe_r","toes_r","r_toe"
],

}

FINGER_KEYWORDS = {

"Thumb":[
    "thumb","pollex"
],

"Index":[
    "index","pointer","finger1"
],

"Middle":[
    "middle","finger2"
],

"Ring":[
    "ring","finger3"
],

"Little":[
    "little","pinky","finger4"
]

}

BODY_CHAINS = [

["LeftShoulder","LeftUpperArm","LeftLowerArm","LeftHand"],
["RightShoulder","RightUpperArm","RightLowerArm","RightHand"],

["LeftUpperLeg","LeftLowerLeg","LeftFoot"],
["RightUpperLeg","RightLowerLeg","RightFoot"]

]

HAND_CHAINS = [

["LeftHand","LeftMiddleProximal","LeftIndexProximal","LeftRingProximal"],
["RightHand","RightMiddleProximal","RightIndexProximal","RightRingProximal"]

]

FINGER_CHAINS = [

["LeftThumbMetacarpal","LeftThumbProximal","LeftThumbDistal"],
["LeftIndexProximal","LeftIndexIntermediate","LeftIndexDistal"],
["LeftMiddleProximal","LeftMiddleIntermediate","LeftMiddleDistal"],
["LeftRingProximal","LeftRingIntermediate","LeftRingDistal"],
["LeftLittleProximal","LeftLittleIntermediate","LeftLittleDistal"],

["RightThumbMetacarpal","RightThumbProximal","RightThumbDistal"],
["RightIndexProximal","RightIndexIntermediate","RightIndexDistal"],
["RightMiddleProximal","RightMiddleIntermediate","RightMiddleDistal"],
["RightRingProximal","RightRingIntermediate","RightRingDistal"],
["RightLittleProximal","RightLittleIntermediate","RightLittleDistal"]

]

# ---------------------------------------------------------
# name normalization
# ---------------------------------------------------------

def normalize(name):

    name=name.lower()

    name=name.replace("_","")
    name=name.replace("-","")
    name=name.replace(".","")
    name=name.replace("mixamorig:","")

    return name

def detect_side(name):

    n=normalize(name)

    if "left" in n or "_l" in name.lower() or ".l" in name.lower():
        return "Left"

    if "right" in n or "_r" in name.lower() or ".r" in name.lower():
        return "Right"

    return None
    
def detect_finger_chain(armature, side, finger):

    bones = armature.data.bones

    finger_keys = {
        "Thumb": ["thumb","pollex"],
        "Index": ["index","finger1","pointer"],
        "Middle": ["middle","finger2"],
        "Ring": ["ring","finger3"],
        "Little": ["little","pinky","finger4"]
    }

    result = [None,None,None]

    for b in bones:

        name = normalize(b.name)

        if side.lower() not in name:
            continue

        for k in finger_keys[finger]:

            if k in name:

                result[0] = b

                # child chain
                if len(b.children) > 0:

                    result[1] = b.children[0]

                    if len(result[1].children) > 0:

                        result[2] = result[1].children[0]

                return result

    return result

class HumanoidAutoDetector:
    def __init__(self, armature_obj):
        self.obj = armature_obj
        self.data = armature_obj.data
        # 缓存 EditBones 及其矩阵
        self.bones = self.data.edit_bones
        self.bone_map = {} # 存储结果: { "Hips": "BoneName", ... }

    def filter_body_lr_pairs_by_chain_and_direction(self, lr_pairs):
        """
        筛选 lr_pairs，保留符合方向一致性且链长足以计算点积的对。
        返回结构与 lr_pairs 一致: [(l_bone, r_bone), ...]
        """
        scored_pairs = []

        for l_bone, r_bone in lr_pairs:
            pb = l_bone.parent
            t_n_l = pb.name.lower()
            if "neck" in t_n_l or "face" in t_n_l or "head" in t_n_l:
                continue
            t_n_l = pb.parent.name.lower()
            if "neck" in t_n_l or "face" in t_n_l or "head" in t_n_l:
                continue
            t_n_l = l_bone.name.lower()
            if "breast" in t_n_l or "boobs" in t_n_l or "chest" in t_n_l:
                continue

            # 找到左侧骨骼起始的最长合法链
            l_chain = self._get_longest_valid_directional_chain(l_bone)
            
            # 严格判定：链长必须 >= 3 才能保证至少有一次有效的连续点积计算
            # 只有一两个骨骼的链被视为“碎骨”，不具备肢体特征
            if l_chain and len(l_chain) >= 3:
                # 记录该对及其链长度，用于后续取最长的两组
                scored_pairs.append({
                    "pair": (l_bone, r_bone),
                    "lchain": l_chain,
                    "length": len(l_chain)
                })

        # 按链长度降序排列
        scored_pairs.sort(key=lambda x: x["length"], reverse=True)

        return scored_pairs

    def _get_longest_valid_directional_chain(self, current_bone):
        """
        递归寻找从当前骨骼开始的最长合法方向链。
        如果在任何位置点积 <= 0，则该分支被截断。
        """
        # 获取所有子分支的路径
        child_paths = []
        
        for child in current_bone.children:
            # 执行点积验证：爷爷->爸爸 dot 爸爸->儿子
            # 只有当爷爷存在时才计算，若不存在（根部）则默认通过
            is_directional_valid = True
            if current_bone.parent:
                # 计算向量
                v_parent = (current_bone.head - current_bone.parent.head).normalized()
                v_child = (child.head - current_bone.head).normalized()
                
                if v_parent.dot(v_child) <= 0:
                    is_directional_valid = False
            
            if is_directional_valid:
                sub_path = self._get_longest_valid_directional_chain(child)
                if sub_path is not None:
                    child_paths.append(sub_path)

        # 如果没有合法的子分支了
        if not child_paths:
            return [current_bone]

        # 返回当前骨骼 + 最长的一条合法子路径
        longest_sub = max(child_paths, key=len)
        return [current_bone] + longest_sub

    def find_all_lr_pairs_under(self, root_bone):
        """
        寻找指定骨骼及其子孙中，所有属于【同一父骨骼】且成对的 L/R 骨骼。
        """
        pairs = []
        # 获取搜索范围：root_bone 本身以及它所有的子孙
        # 我们需要检查这些骨骼作为“父节点”时，其子节点是否存在 L/R 对
        potential_parents = [root_bone] + list(root_bone.children_recursive)
        
        for parent in potential_parents:
            children = parent.children
            if len(children) < 2:
                continue
            
            # 在当前父骨骼的直接子骨骼中寻找对
            checked_in_this_parent = set()
            search_pool = []
            for child in children:
                n_l = child.name.lower()
                if "l" in n_l or "r" in n_l:
                    search_pool.append(child)

            for i, b1 in enumerate(search_pool):
                if b1.name in checked_in_this_parent:
                    continue
                
                for b2 in search_pool[i+1:]:
                    if b2.name in checked_in_this_parent:
                        continue
                    
                    # 只有同一父级下的两个子骨骼名字符合 L/R 差异时才计入
                    if self.check_name_lr_diff(b1.name, b2.name):
                        pairs.append((b1, b2))
                        checked_in_this_parent.add(b1.name)
                        checked_in_this_parent.add(b2.name)
                        break
                        
        return pairs

    def check_name_lr_diff(self, name1, name2):
        """
        基于差异位提取逻辑：
        找出两个字符串中不同的部分，判断该部分是否为 l/r 或 left/right。
        """
        n1 = name1.lower()
        n2 = name2.lower()

        if n1 == n2:
            return False

        # 1. 使用 SequenceMatcher 找出相同部分
        s = difflib.SequenceMatcher(None, n1, n2)
        blocks = s.get_matching_blocks()

        # 2. 提取差异部分
        # 我们假设标准命名的 L/R 骨骼只有一处字符差异
        # 如果块的数量不符合“一段相同-一段不同-一段相同”，说明差异不止一处
        diffs_n1 = []
        diffs_n2 = []
        
        last_i = 0
        last_j = 0
        for i, j, size in blocks:
            # 提取两段相同块之间的差异文本
            if i > last_i:
                diffs_n1.append(n1[last_i:i])
            if j > last_j:
                diffs_n2.append(n2[last_j:j])
            last_i = i + size
            last_j = j + size

        # 3. 判定差异是否符合 L/R 规则
        # 只有当且仅当存在一处差异时才继续（防止完全不相干的骨骼匹配）
        if len(diffs_n1) == 1 and len(diffs_n2) == 1:
            d1 = diffs_n1[0]
            d2 = diffs_n2[0]

            # 定义允许的标识符对
            lr_pairs = [("l", "r"), ("lef", "righ")]
            
            for l_str, r_str in lr_pairs:
                if (d1 == l_str and d2 == r_str) or (d1 == r_str and d2 == l_str):
                    return True

        return False

    def check_hand_chain_consistency(self, lengths):
        """逻辑：所有链长相同，或者只有一个链长度比其他少 1"""
        if not lengths: return False
        max_l = max(lengths)
        min_l = min(lengths)
        if max_l == min_l: return True
        if max_l - min_l == 1:
            # 统计长度少 1 的数量
            return lengths.count(min_l) == 1
        return False

    def detect_fingers(self, hand_bone, side_prefix):
        """识别拇指到小指及其三级骨骼链"""
        fingers = hand_bone.children
        if len(fingers) < 2: return

        # 计算空间距离跨度
        heads = [f.head for f in fingers]
        z_span = max(h.z for h in heads) - min(h.z for h in heads)
        y_span = max(h.y for h in heads) - min(h.y for h in heads)

        # 排序：Z轴大按 Z 排序，Y轴大按 Y 排序
        if z_span > y_span:
            sorted_fingers = sorted(fingers, key=lambda b: b.head.z)
        else:
            sorted_fingers = sorted(fingers, key=lambda b: b.head.y)

        # 映射规则：拇指到小指 [Thumb, Index, Middle, Ring, Little]
        finger_names = ["Thumb", "Index", "Middle", "Ring", "Little"]
        
        # 缺失处理：若少于5根，按顺序忽略：无名指(Ring), 小指(Little), 食指(Index), 大拇指(Thumb)
        ignore_order = ["Ring", "Little", "Index", "Thumb"]
        active_names = finger_names.copy()
        
        while len(sorted_fingers) < len(active_names):
            for to_remove in ignore_order:
                if to_remove in active_names:
                    active_names.remove(to_remove)
                    break

        # 遍历识别的手指
        for i, f_root in enumerate(sorted_fingers):
            f_type = active_names[i]
            # 找到该手指最长子链末端且满足 deform/顶点条件的
            f_chain = self.get_longest_chain(f_root)
            last = -1
            tip = f_chain[-1]
            len_chain = len(f_chain)
            while tip and not (tip.use_deform and self.get_vertex_count(tip.name) > 1):
                last -= 1
                tip = f_chain[last] if last >= -len_chain else None
            if tip:
                # 按父子关系逆推三个等级
                # 注意：拇指是 Metacarpal, Proximal, Distal; 其他是 Proximal, Intermediate, Distal
                suffix = ["Distal", "Intermediate", "Proximal"]
                if f_type == "Thumb":
                    suffix = ["Distal", "Proximal", "Metacarpal"]
                
                curr = tip
                for s in suffix:
                    if curr and curr != hand_bone:
                        self.bone_map[f"{side_prefix}{f_type}{s}"] = curr.name
                        curr = curr.parent

    def map_arm_to_right_side(self):
        """基于左臂识别结果，根据名称差异映射到右臂和右手手指"""
        # 使用 any() 函数配合列表，一次性排除所有下肢关键字
        l_arm_keys = [k for k in self.bone_map.keys() if k.startswith("Left") and not any(x in k for x in ["Leg", "Foot", "Toes"])]

        l_root_name = self.bone_map.get("LeftShoulder")
        r_root_name = self.bone_map.get("RightShoulder")
        
        if not l_root_name or not r_root_name: return

        for key in l_arm_keys:
            l_bone_name = self.bone_map[key]
            r_bone_name = self.find_matching_right_bone(l_root_name, r_root_name, l_bone_name)
            if r_bone_name:
                r_key = key.replace("Left", "Right")
                self.bone_map[r_key] = r_bone_name

    def get_vertex_count(self, bone_name):
        """获取指定骨骼控制的顶点数量 (需要从骨架关联的 Mesh 物体中获取)"""
        # 寻找受此骨架控制的物体
        count = 0
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.parent == self.obj:
                vg = obj.vertex_groups.get(bone_name)
                if vg:
                    for v in obj.data.vertices:
                        for g in v.groups:
                            if g.group == vg.index and g.weight > 0.001:
                                count += 1
        return count

    def get_bones_between(self, start_bone, end_bone):
        """获取 start_bone 和 end_bone 之间的所有骨骼 (不含首尾)"""
        path = []
        curr = end_bone.parent
        while curr and curr != start_bone:
            path.append(curr)
            curr = curr.parent
        return path

    def map_leg_to_right_side(self, l_root, r_root):
        """
        根据 LeftUpperLeg 及其识别出的子骨骼，推导出 Right 侧对应的骨骼。
        使用名称差异映射逻辑。
        """
        # 计算名称差异特征 (例如 "L" -> "R")
        l_name = l_root.name
        r_name = r_root.name

        # 记录映射关系，防止后面查找出错
        leg_keys = ["LeftLowerLeg", "LeftFoot", "LeftToes"]
        for key in leg_keys:
            if key in self.bone_map:
                l_bone_name = self.bone_map[key]
                # 尝试通过替换特征字符找到右侧对应的骨骼名
                # 这里的逻辑是：找出 l_root 和 r_root 的差异点，应用到 l_bone_name 上
                r_bone_name = self.find_matching_right_bone(l_name, r_name, l_bone_name)
                print(f"r_bone_name:{r_bone_name}")
                if r_bone_name:
                    r_key = key.replace("Left", "Right")
                    self.bone_map[r_key] = r_bone_name

    def find_matching_right_bone(self, l_root_name, r_root_name, l_target_name):
        """
        基于根骨骼的差异位置，精准替换目标骨骼中的对称标记。
        修复了 replace 全局替换导致误伤(如 LowerLeg -> RowerReg)的问题。
        """
        import difflib
        
        # 1. 提取根骨骼的差异特征及其位置
        s = difflib.SequenceMatcher(None, l_root_name, r_root_name)
        blocks = s.get_matching_blocks()
        
        diff_l = ""
        diff_r = ""
        diff_pos_in_root = -1 # 记录差异在字符串中开始的位置
        
        last_i = 0
        last_j = 0
        for i, j, size in blocks:
            if i > last_i:
                diff_l = l_root_name[last_i:i]
                diff_r = r_root_name[last_j:j]
                diff_pos_in_root = last_i
                break # 我们只取第一处核心差异（通常是 L/R 标识）
            last_i = i + size
            last_j = j + size
            
        if not diff_l or not diff_r:
            return None

        # 2. 改进的定位替换逻辑
        # 我们不再使用 replace，而是通过正则表达式或精准位置来寻找差异标识

        # 使用正则表达式的 \b (单词边界) 或者前后非字母限定，防止误伤 Leg 里的 L
        # 但最简单有效的办法是：只替换第一次出现的、且符合根骨骼位置特征的 diff_l
        
        def safe_replace(target, old, new):
            # 逻辑：如果标识是特殊的(如 .L, _L, L_), 优先精准匹配
            # 这里我们查找所有匹配项，但为了安全，我们通常认为对称标识在名字中是唯一的
            
            # 查找 old 在 target 中的所有位置
            occurences = [m.start() for m in re.finditer(re.escape(old), target)]
            
            if not occurences:
                return None
                
            # 如果只有一个匹配项，直接替换
            if len(occurences) == 1:
                idx = occurences[0]
                return target[:idx] + new + target[idx + len(old):]
            
            # 如果有多个匹配项（如 Left_LowerLeg），我们优先替换位置最接近根骨骼差异位置的那个
            # 或者按照惯例：通常对称标识位于名字的最前面或最后面
            best_idx = occurences[0]
            # 如果 diff_l 在 root 中靠前，我们也取 target 中靠前的
            if diff_pos_in_root > len(l_root_name) / 2:
                best_idx = occurences[-1]
            
            return target[:best_idx] + new + target[best_idx + len(old):]

        # 执行精准替换
        new_name = safe_replace(l_target_name, diff_l, diff_r)
        
        if new_name and new_name in self.bones:
            return new_name

        # 3. 兜底逻辑：大小写不敏感替换（同样只替换一次）
        target_low = l_target_name.lower()
        dl_low = diff_l.lower()
        
        start_idx = target_low.find(dl_low)
        if start_idx != -1:
            # 构造新名字：只替换找到的第一个位置
            candidate_name = l_target_name[:start_idx] + diff_r + l_target_name[start_idx + len(diff_l):]
            
            # 忽略大小写查找是否存在
            for b_name in self.bones.keys():
                if b_name.lower() == candidate_name.lower():
                    return b_name

        return None

    def get_bone_by_name(self, name, parent_bone=None):
        """
        根据名称列表查找骨骼。
        关键词顺序决定优先级：列表前面的关键词匹配成功会立即返回。
        """
        # 确定搜索范围
        search_pool = parent_bone.children_recursive if parent_bone else self.bones
        
        # 核心修改：外层循环遍历关键词，确保优先级
        for b in search_pool:
            if b.name == name:
                return b
        
        return None

    def get_bone_by_keywords(self, keywords, parent_bone=None):
        """
        根据关键词列表查找骨骼。
        关键词顺序决定优先级：列表前面的关键词匹配成功会立即返回。
        """
        # 确定搜索范围
        search_pool = parent_bone.children_recursive if parent_bone else self.bones
        
        # 核心修改：外层循环遍历关键词，确保优先级
        for k in keywords:
            k_low = k.lower()
            for b in search_pool:
                if k_low in b.name.lower():
                    return b
        
        return None

    def find_lr_arm_pair_in_children(self, parent_bone):
        """
        寻找直接子骨骼中成对的 L/R 骨骼。
        严格按照逻辑：全小写化后，差别为 "l" 和 "r"，或 "left" 和 "right"。
        """
        children = parent_bone.children
        if len(children) < 2:
            return None, None
        search_pool = []
        for child in children:
            n_l = child.name.lower()
            if "breast" in n_l or "boobs" in n_l or "chest" in n_l:
                continue
            elif "l" in n_l or "r" in n_l:
                search_pool.append(child)
        
        # 在当前父骨骼的直接子骨骼中寻找对
        for i, b1 in enumerate(search_pool):
            for b2 in search_pool[i+1:]:
                # 只有同一父级下的两个子骨骼名字符合 L/R 差异时才计入
                if self.check_name_lr_diff(b1.name, b2.name):
                    return b1, b2
                        
        return None, None

    def get_longest_chain(self, start_bone):
        """获取最长子链"""
        if not start_bone.children:
            return [start_bone]
        chains = [self.get_longest_chain(c) for c in start_bone.children]
        return [start_bone] + max(chains, key=len)

    def execute_auto_detect(self, hip_bone_name=None):
        # 1. 寻找 Hips
        if hip_bone_name:
            hips = self.get_bone_by_name(hip_bone_name)
        else:
            hips_keywords = ["hip", "pelvis", "hips", "root", "mixamorig:hips"]
            hips = self.get_bone_by_keywords(hips_keywords)
        if not hips: return None
        self.bone_map["Hips"] = hips.name

        #print(f"第一步结果：{self.bone_map}")

        # --- 2. 寻找腿和躯干 (基于最高链回溯逻辑) ---
        l_upper_leg, r_upper_leg = None, None
        
        # 2a. 筛选合法链
        hips_p = hips.parent or hips
        all_raw_pairs = self.find_all_lr_pairs_under(hips_p)
        longest_lr_chains = self.filter_body_lr_pairs_by_chain_and_direction(all_raw_pairs)
        print(f"longest_lr_chains: {longest_lr_chains}")

        if not longest_lr_chains:
            return None

        # 找到末端最低的链作为腿部
        leg_item = min(longest_lr_chains, key=lambda item: item["lchain"][-1].head.z)
        
        # 寻找“潜在上肢”链：排除掉腿部，且根部高于 Hips
        upper_body_chains = [
            item for item in longest_lr_chains 
            if item != leg_item and item["pair"][0].head.z > hips.head.z
        ]

        for item in longest_lr_chains:
            if item == leg_item:
                l_upper_leg, r_upper_leg = item["pair"][0], item["pair"][1]
                # --- 腿部赋值逻辑 ---
                self.bone_map["LeftUpperLeg"] = l_upper_leg.name
                self.bone_map["RightUpperLeg"] = r_upper_leg.name

        # 2b. 判定 UpperChest 和 Chest (基于最高链回溯)
        if upper_body_chains:
            # 找到根部 (head.z) 位置最高的一组链
            highest_chain_item = max(upper_body_chains, key=lambda item: item["pair"][0].head.z)
            shoulder_l = highest_chain_item["pair"][0]
            
            # 父骨骼作为 UpperChest
            upper_chest = shoulder_l.parent
            if upper_chest and upper_chest != hips and upper_chest != hips_p:
                self.bone_map["UpperChest"] = upper_chest.name
                
                # 爷爷骨骼作为 Chest
                chest = upper_chest.parent
                if chest and chest != hips and chest != hips_p:
                    self.bone_map["Chest"] = chest.name

        #print(f"第二步结果：{self.bone_map}")

        # --- 3. 腿部逻辑 ---
        if l_upper_leg and r_upper_leg:
            self.bone_map["LeftUpperLeg"] = l_upper_leg.name
            self.bone_map["RightUpperLeg"] = r_upper_leg.name

            # 寻找 LeftFoot
            found_toes = False
            # A. 遍历子孙寻找：有两个子骨骼或以上，且所有子骨骼的子骨骼链长度 >= 2 且长度相同
            for b in l_upper_leg.children_recursive:
                if len(b.children) >= 2:
                    chains = [self.get_longest_chain(c) for c in b.children]
                    lengths = [len(ch) for ch in chains]
                    # 逻辑判定：链长 >= 2 且长度全部相同
                    if all(l >= 2 for l in lengths) and len(set(lengths)) == 1:
                        self.bone_map["LeftToes"] = b.name
                        found_toes = True
                        break
            
            # B. 若未找到 Foot，则寻找 LeftToes (最长子链最后一根为 deform 且顶点数 > 1)
            if not found_toes:
                l_leg_chain = self.get_longest_chain(l_upper_leg)
                if l_leg_chain:
                    last_bone = l_leg_chain[-1]
                    # 判定：是变形骨骼 且 控制顶点数 > 1
                    while last_bone and not (last_bone.use_deform and self.get_vertex_count(last_bone.name) > 1):
                        last_bone = last_bone.parent
                    
                    if last_bone:
                        self.bone_map["LeftToes"] = last_bone.name
                        found_toes = True
                            

            # C. 寻找 LeftLowerLeg (处于 LeftUpperLeg 和 LeftFoot 之间)
            if found_toes:
                toes_bone = self.bones[self.bone_map["LeftToes"]]
                if toes_bone.parent:
                    foot_bone = toes_bone.parent
                    if "metatarsals" in foot_bone.name.lower() and foot_bone.parent and "foot" in foot_bone.parent.name.lower():
                        foot_bone = foot_bone.parent
                    self.bone_map["LeftFoot"] = foot_bone.name

                    # 获取两者之间的路径骨骼
                    mid_bones = self.get_bones_between(l_upper_leg, foot_bone)
                    
                    if len(mid_bones) == 1:
                        # 若之间只有一根，直接赋值
                        self.bone_map["LeftLowerLeg"] = mid_bones[0].name
                    elif len(mid_bones) > 1:
                        # 若有多根，寻找垂直位置最靠近两者中间位置的骨骼
                        # 计算 UpperLeg head 和 Foot head 的垂直中点
                        target_z = (l_upper_leg.head.z + foot_bone.head.z) / 2
                        # 找出 Z 轴差距最小的骨骼
                        lower_leg_bone = min(mid_bones, key=lambda b: abs(b.head.z - target_z))
                        self.bone_map["LeftLowerLeg"] = lower_leg_bone.name

            # D. 将左腿结果映射到右腿 (根据名称差异)
            self.map_leg_to_right_side(l_upper_leg, r_upper_leg)

        #print(f"第三步结果：{self.bone_map}")

        # --- 4. 肩臂手及手指逻辑 ---
        # 4a. 寻找 LeftShoulder 和 RightShoulder
        # 逻辑：UpperChest 子骨骼中，名称类似且差异为 "l"/"left" 的为 LeftShoulder
        upper_chest_bone = self.bones.get(self.bone_map.get("UpperChest", ""))
        if upper_chest_bone:
            l_shoulder, r_shoulder = self.find_lr_arm_pair_in_children(upper_chest_bone)
            if l_shoulder and r_shoulder:
                # 判定 LeftShoulder (差异识别已在 find_lr_pair 处理)
                self.bone_map["LeftShoulder"] = l_shoulder.name
                self.bone_map["RightShoulder"] = r_shoulder.name

                # 4b. 寻找 LeftUpperArm 和 LeftLowerArm
                # 逻辑：Shoulder 的最长子链的子骨骼为 UpperArm
                l_shoulder_chain = self.get_longest_chain(l_shoulder)
                if len(l_shoulder_chain) > 1:
                    l_upper_arm = l_shoulder_chain[1] # Shoulder 的子骨骼
                    self.bone_map["LeftUpperArm"] = l_upper_arm.name

                    # 寻找 LeftHand
                    # 逻辑：子孙中找出有两个子骨骼或以上，且子链长匹配的手部骨骼
                    found_hand = False
                    for b in l_upper_arm.children_recursive:
                        if len(b.children) >= 2:
                            chains = [self.get_longest_chain(c) for c in b.children]
                            lengths = [len(ch) for ch in chains]
                            # 条件：链长 >= 3 且 (长度相同 或 仅一个链长度少1)
                            if all(l >= 3 for l in lengths):
                                if self.check_hand_chain_consistency(lengths):
                                    self.bone_map["LeftHand"] = b.name
                                    found_hand = True
                                    break
                    
                    # 若未找到 LeftHand，通过中指逆推
                    if not found_hand:
                        # 逻辑：最长子链末端为 deform 且顶点 > 1 的为中指末端
                        full_arm_chain = self.get_longest_chain(l_upper_arm)
                        tip = full_arm_chain[-1]
                        if tip.use_deform and self.get_vertex_count(tip.name) > 1:
                            # 依次为：末端 -> 中间(Distal) -> 根部(Proximal) -> 手(Hand)
                            # 假设：Tip(Distal) -> Parent(Intermediate) -> Parent(Proximal) -> Parent(Hand)
                            p1 = tip.parent # Intermediate
                            p2 = p1.parent if p1 else None # Proximal
                            p3 = p2.parent if p2 else None # Hand
                            if p3:
                                self.bone_map["LeftHand"] = p3.name
                                found_hand = True

                    # 4c. 寻找 LeftLowerArm
                    if found_hand:
                        hand_bone = self.bones[self.bone_map["LeftHand"]]
                        mid_arm_bones = self.get_bones_between(l_upper_arm, hand_bone)
                        if len(mid_arm_bones) == 1:
                            self.bone_map["LeftLowerArm"] = mid_arm_bones[0].name
                        elif len(mid_arm_bones) > 1:
                            # 逻辑：水平位置 (X轴) 最靠近中间的
                            target_x = (l_upper_arm.head.x + hand_bone.head.x) / 2
                            lower_arm = min(mid_arm_bones, key=lambda b: abs(b.head.x - target_x))
                            self.bone_map["LeftLowerArm"] = lower_arm.name

                        # 4d. 手指识别逻辑
                        self.detect_fingers(hand_bone, "Left")

            # 4e. 映射到右侧
            self.map_arm_to_right_side()

        #print(f"第四步结果：{self.bone_map}")

        # --- 5. 颈部与头部逻辑 ---
        # 逻辑：根据 UpperChest 最长子链依次找到 Neck 和 Head
        if "UpperChest" in self.bone_map:
            upper_chest_bone = self.bones[self.bone_map["UpperChest"]]
            
            # 获取 UpperChest 向上延伸的最长子链
            # 注意：需排除已经识别为肩膀（Shoulder）的分支
            neck_head_candidates = []
            for child in upper_chest_bone.children:
                if child.name != self.bone_map.get("LeftShoulder") and \
                   child.name != self.bone_map.get("RightShoulder"):
                    neck_head_candidates.append(child)
            
            if neck_head_candidates:
                # 取其中最长的子链作为脖子和头的主干
                main_neck_chain = self.get_longest_chain(max(neck_head_candidates, key=lambda c: len(self.get_longest_chain(c))))
                
                # A. 优先尝试根据名称小写化寻找 "neck" 和 "head"
                found_neck = self.get_bone_by_keywords(["neck"], parent_bone=upper_chest_bone)
                found_head = self.get_bone_by_keywords(["head"], parent_bone=upper_chest_bone)
                
                if found_neck:
                    self.bone_map["Neck"] = found_neck.name
                if found_head:
                    self.bone_map["Head"] = found_head.name
                
                # B. 若未通过名字找到，执行层级逻辑
                if "Neck" not in self.bone_map and len(main_neck_chain) >= 1:
                    # UpperChest 最长子链第一个子骨骼为 Neck
                    self.bone_map["Neck"] = main_neck_chain[0].name
                
                if "Head" not in self.bone_map and "Neck" in self.bone_map:
                    neck_bone = self.bones[self.bone_map["Neck"]]
                    # Neck 的子骨骼中名称找不到 "neck" 关键字的最近子代骨骼为 Head
                    for b in neck_bone.children_recursive:
                        if "neck" not in b.name.lower():
                            self.bone_map["Head"] = b.name
                            break

                head_bone = self.bones[self.bone_map["Head"]]
                if head_bone:
                    # 遍历所有head子骨骼找到jaw和eyes
                    for child in head_bone.children:
                        n_l = child.name.lower()
                        if "jaw" in n_l:
                            self.bone_map["Jaw"] = child.name
                            break
                    lr_pairs = self.find_all_lr_pairs_under(head_bone)
                    for l_bone, r_bone in lr_pairs:
                        if "eye" in l_bone.name.lower():
                            self.bone_map["LeftEye"] = l_bone.name
                            self.bone_map["RightEye"] = r_bone.name
                            break
  
        #print(f"第五步结果：{self.bone_map}")

        # --- 6. 胸部与脊椎逻辑 ---
        # 逻辑：确定 Chest 和 Spine 的最终归属
        hips_bone = self.bones[self.bone_map["Hips"]]
        upper_chest_name = self.bone_map.get("UpperChest")
        
        if upper_chest_name:
            upper_chest_bone = self.bones[upper_chest_name]
            
            # A. 确定 Chest
            # 若之前识别肩部时已经找到了 Chest 则忽略；若未找到，UpperChest 的父骨骼为 Chest
            if "Chest" not in self.bone_map:
                parent = upper_chest_bone.parent
                if parent and parent != hips_bone:
                    self.bone_map["Chest"] = parent.name
            
            # B. 确定 Spine
            # 在 Chest (或 UpperChest) 和 Hips 骨骼链中，Hips 的子骨骼为 Spine
            target_top_bone = None
            if "Chest" in self.bone_map:
                target_top_bone = self.bones[self.bone_map["Chest"]]
            else:
                target_top_bone = upper_chest_bone
                
            # 获取从 Hips 到该胸部骨骼的路径
            spine_path = self.get_bones_between(hips_bone, target_top_bone)
            # 逻辑：Hips 的子骨骼为 Spine。在路径中，最靠近 Hips 的即为 Hips 的直接子级
            if spine_path:
                # path 是从上往下倒序的 (End -> Start)，所以最后一根是 Hips 的子骨骼
                self.bone_map["Spine"] = spine_path[-1].name
            else:
                # 如果中间没有骨骼，且 Chest/UpperChest 直接连在 Hips 上
                if target_top_bone.parent == hips_bone:
                    # 这种特殊情况下，如果必须有一个 Spine，通常将该骨骼同时视为 Spine 或保持空
                    # 按照你的逻辑：Hips 的子骨骼为 Spine
                    self.bone_map["Spine"] = target_top_bone.name
        #print(f"第六步结果：{self.bone_map}")

        return self.bone_map

    def assign_to_scene(self, context, is_source=True):
        s = context.scene.humanoid_settings
        for item in s.bone_items:
            standard_name = item.humanoid # 例如 "LeftUpperArm"
            detected_name = self.bone_map.get(standard_name)
            
            if detected_name:
                if is_source:
                    item.source = detected_name
                else:
                    item.target = detected_name

def apply_to_humanoid_settings(context, armature_obj, is_source=True, hip_bone_name=None):
    """
    将识别结果写入 context.scene.humanoid_settings.bone_items
    mode: 'source' 或 'target'
    """
    detector = HumanoidAutoDetector(armature_obj)
    # 切换到编辑模式以读取坐标
    original_mode = armature_obj.mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    results = detector.execute_auto_detect(hip_bone_name)
    
    bpy.ops.object.mode_set(mode=original_mode)
    
    if not results:
        return

    detector.assign_to_scene(context, is_source)


# ---------------------------------------------------------
# Mapping item
# ---------------------------------------------------------

class HUMANOID_BoneItem(PropertyGroup):

    humanoid: StringProperty()

    source: StringProperty()

    target: StringProperty()


# ---------------------------------------------------------
# Armature selector
# ---------------------------------------------------------

def armature_poll(self,obj):
    return obj.type == "ARMATURE"


class HUMANOID_Settings(PropertyGroup):

    source_armature: PointerProperty(
        name="Source",
        type=bpy.types.Object,
        poll=armature_poll,
        update=lambda s,c: auto_fill_source(c)
    )

    target_armature: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        poll=armature_poll,
        update=lambda s,c: auto_fill_target(c)
    )

    bone_items: CollectionProperty(type=HUMANOID_BoneItem)

    index: IntProperty()


# ---------------------------------------------------------
# autofill
# ---------------------------------------------------------

def auto_fill_source(context):

    s = context.scene.humanoid_settings
    arm = s.source_armature

    if not arm:
        for i in s.bone_items:
            i.source = ""
        return

    apply_to_humanoid_settings(context, arm, True)


def auto_fill_target(context):

    s = context.scene.humanoid_settings
    arm = s.target_armature

    if not arm:
        for i in s.bone_items:
            i.target = ""
        return

    apply_to_humanoid_settings(context, arm, False)


# ---------------------------------------------------------
# UI List
# ---------------------------------------------------------

class HUMANOID_UL_List(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        row = layout.row(align=True)

        row.label(text=item.humanoid)

        row.prop_search(
            item,
            "source",
            context.scene.humanoid_settings.source_armature.data if context.scene.humanoid_settings.source_armature else bpy.data.armatures[0],
            "bones",
            text=""
        )

        row.prop_search(
            item,
            "target",
            context.scene.humanoid_settings.target_armature.data if context.scene.humanoid_settings.target_armature else bpy.data.armatures[0],
            "bones",
            text=""
        )

# ---------------------------------------------------------
# Detector Operators
# ---------------------------------------------------------

class HUMANOID_OT_DetectSourceByHip(Operator):

    bl_idname = "humanoid.detect_source_by_hip"
    bl_label = "Detect Source Humanoid by Hips"

    def execute(self,context):

        s = context.scene.humanoid_settings
        arm = s.source_armature

        if not arm:
            return {'CANCELLED'}

        hip_bone_name = None
        for i in s.bone_items:
            if i.humanoid == "Hips":
                hip_bone_name = i.source

        apply_to_humanoid_settings(context, arm, True, hip_bone_name)

        return {'FINISHED'}

class HUMANOID_OT_DetectTargetByHip(Operator):

    bl_idname = "humanoid.detect_target_by_hip"
    bl_label = "Detect Target Humanoid by Hips"

    def execute(self,context):

        s = context.scene.humanoid_settings
        arm = s.target_armature

        if not arm:
            return {'CANCELLED'}

        hip_bone_name = None
        for i in s.bone_items:
            if i.humanoid == "Hips":
                hip_bone_name = i.target

        apply_to_humanoid_settings(context, arm, False, hip_bone_name)

        return {'FINISHED'}

# ---------------------------------------------------------
# Rename Operators
# ---------------------------------------------------------

class HUMANOID_OT_RenameSourceToHumanoid(Operator):

    bl_idname = "humanoid.rename_source_humanoid"
    bl_label = "Rename Source To Humanoid"

    def execute(self,context):

        s = context.scene.humanoid_settings
        arm = s.source_armature

        if not arm:
            return {'CANCELLED'}

        for i in s.bone_items:

            if i.source in arm.data.bones:

                arm.data.bones[i.source].name = i.humanoid
                i.source = i.humanoid

        return {'FINISHED'}


class HUMANOID_OT_RenameTargetToHumanoid(Operator):

    bl_idname = "humanoid.rename_target_humanoid"
    bl_label = "Rename Target To Humanoid"

    def execute(self,context):

        s = context.scene.humanoid_settings
        arm = s.target_armature

        if not arm:
            return {'CANCELLED'}

        for i in s.bone_items:

            if i.target in arm.data.bones:

                arm.data.bones[i.target].name = i.humanoid
                i.target = i.humanoid

        return {'FINISHED'}


class HUMANOID_OT_SourceToTarget(Operator):

    bl_idname = "humanoid.source_to_target"
    bl_label = "Rename Source To Target"

    def execute(self,context):

        s = context.scene.humanoid_settings
        arm = s.source_armature

        for i in s.bone_items:

            if i.source and i.target:

                arm.data.bones[i.source].name = i.target
                i.source = i.target

        return {'FINISHED'}


class HUMANOID_OT_TargetToSource(Operator):

    bl_idname = "humanoid.target_to_source"
    bl_label = "Rename Target To Source"

    def execute(self,context):

        s = context.scene.humanoid_settings
        arm = s.target_armature

        for i in s.bone_items:

            if i.source and i.target:

                arm.data.bones[i.target].name = i.source
                i.target = i.source

        return {'FINISHED'}


# ---------------------------------------------------------
# Retarget logic
# ---------------------------------------------------------

class HUMANOID_OT_AlignPose(bpy.types.Operator):
    bl_idname = "humanoid.align_pose"
    bl_label = "Align Target Pose (Godot)"

    def execute(self,context):
        s = context.scene.humanoid_settings
        src = s.source_armature
        dst = s.target_armature

        if not src or not dst:
            return {'CANCELLED'}

        bpy.context.view_layer.objects.active = dst
        bpy.ops.object.mode_set(mode='POSE')

        # 传入context而非src/dst
        align_all(context)

        return {'FINISHED'}


class HUMANOID_OT_ApplyRest(Operator):
    bl_idname = "humanoid.apply_rest"
    bl_label = "Apply Rest Pose (Keep Mesh)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        # 确保我们拿到的是当前的骨架
        arm_obj = context.active_object
        if not arm_obj or arm_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "请选中一个骨架对象")
            return {'CANCELLED'}

        # 1. 查找所有绑定到该骨架的 Mesh 对象
        affected_meshes = []
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE' and mod.object == arm_obj:
                        affected_meshes.append((obj, mod))
                        break

        # 2. 应用 Mesh 的修改器
        # 我们需要先切回 Object 模式来应用修改器
        bpy.ops.object.mode_set(mode='OBJECT')
        
        for mesh_obj, mod in affected_meshes:
            # 选中该 Mesh 设为活动对象
            context.view_layer.objects.active = mesh_obj
            # 应用修改器（这会让模型顶点永久固定在当前姿态）
            bpy.ops.object.modifier_apply(modifier=mod.name)
            
        # 3. 应用骨架的 Pose 为 Rest Pose
        context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply()
        bpy.ops.object.mode_set(mode='OBJECT')

        # 4. 重新为 Mesh 添加 Armature 修改器
        for mesh_obj, _ in affected_meshes:
            new_mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
            new_mod.object = arm_obj
            new_mod.use_vertex_groups = True
            # 如果你有特定的设置（如多层变形），可以在这里添加

        self.report({'INFO'}, f"已同步 {len(affected_meshes)} 个模型的 Rest Pose")
        return {'FINISHED'}


class HUMANOID_OT_CopyRoll(Operator):
    bl_idname = "humanoid.copy_roll"
    bl_label = "Copy Bone Roll & Keep Children"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.humanoid_settings
        src = s.source_armature
        dst = s.target_armature

        if not src or not dst:
            self.report({'ERROR'}, "未指定源或目标骨架")
            return {'CANCELLED'}

        # --- 1. 记录子对象变换 ---
        child_data = {obj: obj.matrix_world.copy() for obj in bpy.data.objects if obj.parent == dst}

        # --- 2. 准备源数据 ---
        src_bone_matrices = {}
        # 切换到源骨架取数据
        context.view_layer.objects.active = src
        bpy.ops.object.mode_set(mode='EDIT')
        for i in s.bone_items:
            sb = src.data.edit_bones.get(i.source)
            if sb:
                src_bone_matrices[i.source] = sb.matrix.copy()
        
        # --- 3. 目标骨架操作 ---
        context.view_layer.objects.active = dst
        bpy.ops.object.mode_set(mode='EDIT')
        
        # --- 【核心修复】：按层级深度排序 ---
        # 这样能保证 parent 一定比 child 先处理
        def get_bone_depth(item):
            tb = dst.data.edit_bones.get(item.target)
            if tb:
                return len(tb.parent_recursive)
            return 0

        # 按深度从小到大排序（Root骨骼深度为0，最先处理）
        sorted_items = sorted(s.bone_items, key=get_bone_depth)

        for i in sorted_items:
            sb_matrix = src_bone_matrices.get(i.source)
            tb = dst.data.edit_bones.get(i.target)

            if sb_matrix and tb:
                # 记录原始长度
                orig_length = tb.length
                
                # A. 对齐方向 (Y轴)
                # 注意：如果骨骼是 Connected 状态，修改父骨骼 tail 会带动子骨骼 head
                # 按顺序处理可以保证这种连锁反应是受控的
                src_dir = sb_matrix.to_3x3().col[1].normalized()
                tb.tail = tb.head + src_dir * orig_length
                
                # B. 对齐 Roll
                src_x_axis = sb_matrix.to_3x3().col[0]
                tb.align_roll(src_x_axis)

        # 刷新并退出模式
        bpy.ops.object.mode_set(mode='OBJECT')

        # --- 4. 还原变换 ---
        for obj, original_matrix in child_data.items():
            obj.matrix_world = original_matrix

        self.report({'INFO'}, "已按层级顺序完成对齐")
        return {'FINISHED'}

# ---------------------------------------------------------
# JSON
# ---------------------------------------------------------

class HUMANOID_OT_ExportSource(Operator, ExportHelper):

    bl_idname = "humanoid.export_source"
    bl_label = "Export Source JSON"

    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self,context):

        s = context.scene.humanoid_settings

        data = {i.humanoid:i.source for i in s.bone_items}

        with open(self.filepath, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        self.report({'INFO'}, f"Successfully exported to {self.filepath}")

        return {'FINISHED'}


class HUMANOID_OT_ImportSource(Operator, ImportHelper):

    bl_idname = "humanoid.import_source"
    bl_label = "Import Source JSON"

    filepath: StringProperty(
        name="File Path",
        description="Path to the JSON file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self,context):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            s = context.scene.humanoid_settings
            
            data = json.load(open(self.filepath))

            for i in s.bone_items:

                if i.humanoid in data:

                    i.source = data[i.humanoid]
            
            self.report({'INFO'}, f"Successfully imported: {self.filepath}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load JSON: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        # --- 核心修复代码 ---
        # 获取当前 .blend 文件的基础路径 (不带后缀)
        # 如果文件没保存，blend_filepath 会是空的
        blend_filepath = bpy.data.filepath
        if blend_filepath:
            # 拿到文件名（去后缀），然后加上你的 .json
            base_name = os.path.splitext(blend_filepath)[0]
            self.filepath = base_name + ".json"
        else:
            # 如果是未保存的新项目，给个默认名
            self.filepath = "humanoid_data.json"
        # -------------------

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class HUMANOID_OT_ExportTarget(Operator, ExportHelper):

    bl_idname = "humanoid.export_target"
    bl_label = "Export Target JSON"

    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self,context):

        s = context.scene.humanoid_settings

        data = {i.humanoid:i.target for i in s.bone_items}

        with open(self.filepath, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        self.report({'INFO'}, f"Successfully exported to {self.filepath}")

        return {'FINISHED'}


class HUMANOID_OT_ImportTarget(Operator, ImportHelper):

    bl_idname = "humanoid.import_target"
    bl_label = "Import Target JSON"

    filepath: StringProperty(
        name="File Path",
        description="Path to the JSON file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self,context):
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            s = context.scene.humanoid_settings
            
            data = json.load(open(self.filepath))

            for i in s.bone_items:

                if i.humanoid in data:

                    i.target = data[i.humanoid]
            
            self.report({'INFO'}, f"Successfully imported: {self.filepath}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load JSON: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        # --- 核心修复代码 ---
        # 获取当前 .blend 文件的基础路径 (不带后缀)
        # 如果文件没保存，blend_filepath 会是空的
        blend_filepath = bpy.data.filepath
        if blend_filepath:
            # 拿到文件名（去后缀），然后加上你的 .json
            base_name = os.path.splitext(blend_filepath)[0]
            self.filepath = base_name + ".json"
        else:
            # 如果是未保存的新项目，给个默认名
            self.filepath = "humanoid_data.json"
        # -------------------

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

@persistent
def humanoid_init(dummy):

    for scene in bpy.data.scenes:

        s = scene.humanoid_settings

        if len(s.bone_items) == 0:

            for b in HUMANOID_BONES:

                item = s.bone_items.add()
                item.humanoid = b

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

class HUMANOID_PT_Main(Panel):

    bl_label = "Humanoid Retarget"
    bl_idname = "HUMANOID_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Humanoid"

    def draw(self,context):

        layout = self.layout
        scene = context.scene

        ensure_bone_items(scene)

        s = scene.humanoid_settings

        layout.prop(s, "source_armature")
        layout.prop(s, "target_armature")

        layout.template_list(
            "HUMANOID_UL_List",
            "",
            s,
            "bone_items",
            s,
            "index",
            rows=12
        )

        col = layout.column(align=True)

        col.label(text="Detector")

        col.operator("humanoid.detect_source_by_hip")
        col.operator("humanoid.detect_target_by_hip")

        col.label(text="Rename")

        col.operator("humanoid.rename_source_humanoid")
        col.operator("humanoid.rename_target_humanoid")
        col.operator("humanoid.source_to_target")
        col.operator("humanoid.target_to_source")

        col.separator()

        col.label(text="Retarget")

        col.operator("humanoid.align_pose")
        col.operator("humanoid.apply_rest")
        col.operator("humanoid.copy_roll")

        col.separator()

        col.label(text="Config")

        col.operator("humanoid.export_source")
        col.operator("humanoid.import_source")
        col.operator("humanoid.export_target")
        col.operator("humanoid.import_target")

def align_bone_direction(context, bone_humanoid_a, bone_humanoid_b):
    humanoid_settings = context.scene.humanoid_settings
    src_arm = humanoid_settings.source_armature
    dst_arm = humanoid_settings.target_armature

    # 获取骨骼
    bone_item_a = next((i for i in humanoid_settings.bone_items if i.humanoid == bone_humanoid_a), None)
    bone_item_b = next((i for i in humanoid_settings.bone_items if i.humanoid == bone_humanoid_b), None)

    if bone_item_a == None or bone_item_a.source == None or bone_item_a.target == None or bone_item_b == None or bone_item_b.source == None or bone_item_b.target == None:
        return
    
    src_a = src_arm.pose.bones.get(bone_item_a.source)
    src_b = src_arm.pose.bones.get(bone_item_b.source)
    dst_a = dst_arm.pose.bones.get(bone_item_a.target)
    dst_b = dst_arm.pose.bones.get(bone_item_b.target)

    # 1. 计算当前的向量方向
    src_dir = (src_b.head - src_a.head).normalized()
    dst_dir_before = (dst_b.head - dst_a.head).normalized()

    print("="*50)
    print(f"对齐：{bone_humanoid_a} -> {bone_humanoid_b}")

    # 2. 计算骨架空间旋转增量 q
    q_diff_arm = dst_dir_before.rotation_difference(src_dir)

    # 3. 构造目标的【骨架空间矩阵】 (Matrix Armature)
    # 保持 A 的位置和缩放，只应用旋转增量
    old_loc = dst_a.matrix.to_translation()
    old_scale = dst_a.matrix.to_scale()
    new_rot_mtx = q_diff_arm.to_matrix() @ dst_a.matrix.to_3x3()
    
    target_matrix_arm = Matrix.LocRotScale(old_loc, new_rot_mtx, old_scale)

    # 4. 核心转换：Armature Space -> Pose Space (matrix_basis)
    # 根据 Blender 文档，pose_bone.matrix = parent.matrix @ bone.matrix_local.relative @ matrix_basis
    # 我们推导 matrix_basis 的唯一可靠方式是：
    if dst_a.parent:
        # 获取 A 的 Edit Bone 相对于父级 Edit Bone 的矩阵 (Rest Pose 局部矩阵)
        # 公式：M_Edit_Local = Parent_Edit_Global_Inv @ Child_Edit_Global
        m_edit_local = dst_a.parent.bone.matrix_local.inverted() @ dst_a.bone.matrix_local
        
        # 计算当前的 Pose 局部矩阵
        # 公式：M_Basis = (Parent_Pose_Global @ M_Edit_Local).inverted() @ Target_Pose_Global
        new_matrix_basis = (dst_a.parent.matrix @ m_edit_local).inverted() @ target_matrix_arm
    else:
        # 如果没有父级，直接抵消 Edit Mode 的全局偏移
        new_matrix_basis = dst_a.bone.matrix_local.inverted() @ target_matrix_arm

    # 5. 应用旋转到四元数
    dst_a.rotation_mode = 'QUATERNION'
    dst_a.rotation_quaternion = new_matrix_basis.to_quaternion()

    # 必须更新，否则后续计算或日志获取的坐标是旧的
    context.view_layer.update()

    # --- 打印日志 ---
    dst_dir_after = (dst_b.head - dst_a.head).normalized()
    print(f"[源方向]       {src_dir}")
    print(f"[目标方向-后]  {dst_dir_after}")
    print(f"[误差距离]     {(src_dir - dst_dir_after).length:.8f}")
    print("="*50)

def align_hand_chain(context, bone_humanoid_a, bone_humanoid_b, bone_humanoid_c, bone_humanoid_d):
    """
    手部骨骼链对齐：
    A -> 旋转中心 (如肩/大臂/手腕)
    B -> 目标指向点 (如肘/前臂/中指根)
    C -> 弯曲参考点 (如手肘/相邻手指) 用于确定旋转平面（Roll）
    """
    humanoid_settings = context.scene.humanoid_settings
    src_arm = humanoid_settings.source_armature
    dst_arm = humanoid_settings.target_armature
    
    if not src_arm or not dst_arm:
        return
    
    # 1. 获取映射项
    bone_item_a = next((i for i in humanoid_settings.bone_items if i.humanoid == bone_humanoid_a), None)
    bone_item_b = next((i for i in humanoid_settings.bone_items if i.humanoid == bone_humanoid_b), None)
    bone_item_c = next((i for i in humanoid_settings.bone_items if i.humanoid == bone_humanoid_c), None)
    
    if not (bone_item_a and bone_item_b and bone_item_c):
        return
    
    # 2. 获取 PoseBone (必须用 PoseBone 才能拿到当前实时的 head 坐标)
    psrcA = src_arm.pose.bones.get(bone_item_a.source)
    psrcB = src_arm.pose.bones.get(bone_item_b.source)
    psrcC = src_arm.pose.bones.get(bone_item_c.source)
    
    pdstA = dst_arm.pose.bones.get(bone_item_a.target)
    pdstB = dst_arm.pose.bones.get(bone_item_b.target)
    pdstC = dst_arm.pose.bones.get(bone_item_c.target)

    if not all([psrcA, psrcB, psrcC, pdstA, pdstB, pdstC]):
        return

    # -------------------------- 核心逻辑：构造源骨骼的目标矩阵 --------------------------
    # 在骨架空间构造一个理想的 3x3 矩阵
    # Y轴：A指向B (Blender骨骼主轴是Y)
    # X轴/Z轴：由 A-B 和 A-C 构成的平面决定
    
    def get_align_matrix(pA, pB, pC):
        dir_y = (pB.head - pA.head).normalized()  # 主轴
        dir_temp = (pC.head - pA.head).normalized()
        
        # 叉乘得到侧轴
        dir_x = dir_temp.cross(dir_y).normalized()
        dir_z = dir_y.cross(dir_x).normalized()
        
        # 构造 3x3 矩阵 (列向量排列)
        return Matrix((dir_x, dir_y, dir_z)).transposed()

    # 源骨骼当前的理想世界(骨架)旋转
    src_rot_arm = get_align_matrix(psrcA, psrcB, psrcC)
    
    # 目标骨骼当前的理想世界(骨架)旋转
    dst_rot_arm_current = get_align_matrix(pdstA, pdstB, pdstC)
    
    # 计算从“当前目标旋转”到“源旋转”的偏差
    # q_diff * dst_rot = src_rot  =>  q_diff = src_rot * dst_rot_inv
    q_diff_arm = src_rot_arm @ dst_rot_arm_current.inverted()

    # -------------------------- 空间转换与应用 --------------------------
    # 构造目标 4x4 矩阵 (保持位置不动)
    target_matrix_arm = q_diff_arm.to_4x4() @ pdstA.matrix

    # 关键：应用我们在单根骨骼对齐中成功的“公式”
    # 抵消父级姿态和自身 Edit Mode (Rest Pose) 的基准
    if pdstA.parent:
        # 计算相对于父级的 Edit 偏移
        m_edit_local = pdstA.parent.bone.matrix_local.inverted() @ pdstA.bone.matrix_local
        # 转回 Pose Basis 空间
        new_matrix_basis = (pdstA.parent.matrix @ m_edit_local).inverted() @ target_matrix_arm
    else:
        new_matrix_basis = pdstA.bone.matrix_local.inverted() @ target_matrix_arm

    # 写入旋转
    pdstA.rotation_mode = 'QUATERNION'
    pdstA.rotation_quaternion = new_matrix_basis.to_quaternion()

    # 刷新
    context.view_layer.update()
    
    print(f"链式对齐完成: {bone_humanoid_a}")

def align_all(context):
    # 从context获取humanoid设置
    humanoid_settings = context.scene.humanoid_settings
    src = humanoid_settings.source_armature
    dst = humanoid_settings.target_armature
    
    if not src or not dst:
        return

    for chain in BODY_CHAINS:
        for i in range(len(chain)-1):
            align_bone_direction(context, chain[i], chain[i+1])
    
    for chain in HAND_CHAINS:
        align_hand_chain(context, *chain)
    
    for chain in FINGER_CHAINS:
        for i in range(len(chain)-1):
            align_bone_direction(context, chain[i], chain[i+1])

# ---------------------------------------------------------
# register
# ---------------------------------------------------------

classes = [

    HUMANOID_BoneItem,
    HUMANOID_Settings,

    HUMANOID_UL_List,

    HUMANOID_OT_DetectSourceByHip,
    HUMANOID_OT_DetectTargetByHip,

    HUMANOID_OT_RenameSourceToHumanoid,
    HUMANOID_OT_RenameTargetToHumanoid,
    HUMANOID_OT_SourceToTarget,
    HUMANOID_OT_TargetToSource,

    HUMANOID_OT_AlignPose,
    HUMANOID_OT_ApplyRest,
    HUMANOID_OT_CopyRoll,

    HUMANOID_OT_ExportSource,
    HUMANOID_OT_ImportSource,
    HUMANOID_OT_ExportTarget,
    HUMANOID_OT_ImportTarget,

    HUMANOID_PT_Main
]

def ensure_bone_items(scene):

    s = scene.humanoid_settings

    if len(s.bone_items) == 0:

        for b in HUMANOID_BONES:

            item = s.bone_items.add()
            item.humanoid = b

def register():

    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.humanoid_settings = PointerProperty(type=HUMANOID_Settings)

    bpy.app.handlers.load_post.append(humanoid_init)


def unregister():

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.humanoid_settings


if __name__ == "__main__":
    register()