INSERT INTO `feed_type` VALUES (1, '提出了问题');
INSERT INTO `feed_type` VALUES (2, '回答了问题');
INSERT INTO `feed_type` VALUES (3, '关注了问题');
INSERT INTO `feed_type` VALUES (4, '下很多人关注了问题');
INSERT INTO `feed_type` VALUES (5, '赞同了回答');
INSERT INTO `feed_type` VALUES (6, '下很多人赞同了回答');
INSERT INTO `feed_type` VALUES (7, '发布了文章');
INSERT INTO `feed_type` VALUES (8, '评论了文章');
INSERT INTO `feed_type` VALUES (9, '喜欢了文章');
INSERT INTO `feed_type` VALUES (10, '下很多人喜欢了文章');
INSERT INTO `feed_type` VALUES (11, '赞同了评论');
INSERT INTO `feed_type` VALUES (12, '下很多人赞同了评论');




问答：

user 提出了问题
user 回答了问题
user 关注了问题
tag 下很多人关注了问题
user 赞同了回答
tag 下很多人赞同了回答




文章：

user 发布了文章
user 评论了文章
user 喜欢了文章
tag 下很多人喜欢了文章
user 赞同了评论
tag 下很多人赞同了评论


`id` `user_id` `tag_id` `post_id` `reply_id` `feed_type` `created`


       gao                 1                      1

       gao                 1            1         2

       gao                 1                      3

       gao                 1            1         5


                   1       1                      4

                   1       1             1        6




       gao                 2                      7

       gao                 2            2         8

       gao                 2                      9

       gao                 2            2         11