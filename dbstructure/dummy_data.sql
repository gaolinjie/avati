



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
user 收藏了文章
tag 下很多人收藏了文章
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



`id` `author_id` `user_id` `post_id` `reply_id` `notice_type` `created`
      me          gao       1         1          1
      me          gao       1                    2
      me          gao       1                    3
      me          gao       1         1          4
      me          gao       1         1          5
      me          gao       1                    6
      me          gao       1         1          7


      me          gao                            15


INSERT INTO `notice_type` VALUES (1, '回答了你的问题');
INSERT INTO `notice_type` VALUES (4, '赞同了你的回答');
INSERT INTO `notice_type` VALUES (5, '感谢了你的回答');
INSERT INTO `notice_type` VALUES (8, '评论了你的文章');
INSERT INTO `notice_type` VALUES (11, '赞同了你的评论');
INSERT INTO `notice_type` VALUES (12, '感谢了你的评论');
INSERT INTO `notice_type` VALUES (7, '在回答中提到了你');
INSERT INTO `notice_type` VALUES (14, '在评论中提到了你');



INSERT INTO `notice_type` VALUES (2, '关注了你的问题');
INSERT INTO `notice_type` VALUES (3, '感谢了你的问题');
INSERT INTO `notice_type` VALUES (9, '收藏了你的文章');
INSERT INTO `notice_type` VALUES (10, '感谢了你的文章');
INSERT INTO `notice_type` VALUES (16, '赞了你的问题');
INSERT INTO `notice_type` VALUES (17, '赞了你的文章');



INSERT INTO `notice_type` VALUES (6, '在问题中提到了你');
INSERT INTO `notice_type` VALUES (13, '在文章中提到了你');



INSERT INTO `notice_type` VALUES (15, '关注了你');






INSERT INTO `feed_type` VALUES (1, '提出了问题');
INSERT INTO `feed_type` VALUES (3, '关注了问题');
INSERT INTO `feed_type` VALUES (4, '下很多人关注了问题');
INSERT INTO `feed_type` VALUES (7, '发布了文章');
INSERT INTO `feed_type` VALUES (9, '收藏了文章');
INSERT INTO `feed_type` VALUES (10, '下很多人收藏了文章');
INSERT INTO `feed_type` VALUES (13, '赞了问题');
INSERT INTO `feed_type` VALUES (14, '下很多人赞了问题');
INSERT INTO `feed_type` VALUES (15, '赞了文章');
INSERT INTO `feed_type` VALUES (16, '下很多人赞了文章');


INSERT INTO `feed_type` VALUES (2, '回答了问题');
INSERT INTO `feed_type` VALUES (5, '赞同了回答');
INSERT INTO `feed_type` VALUES (6, '下很多人赞同了回答');
INSERT INTO `feed_type` VALUES (8, '评论了文章');
INSERT INTO `feed_type` VALUES (11, '赞同了评论');
INSERT INTO `feed_type` VALUES (12, '下很多人赞同了评论')



初始资本 2000                    获得初始资本     null           2000 铜币           null
创建主题  -20                      创建了                 null               主题                   post
创建回复 -5                         创建了                 null              回复                    post+reply_id
主题回复收益 +5                        收到                     user             的回复                post+reply_id
赞同别人 -1                         发送对                user              的赞同                post or post+reply_id
收到赞同 +1                        收到                    user             的赞同                  post or post +reply_id
撤销赞同 +1               撤销对                 user            的赞同                   post or post +reply_id
赞同被撤销 -1            赞同被                      user           撤销           post or post +reply_id
发送谢意 -10                       发送对                user            的谢意                  post or post+reply_id
收到谢意 +10                      收到                   user                的谢意              post or post+reply_id
发送邀请 -10                       发送                   null             邀请                       null
邀请成功 +100                   邀请                    user            成功                      null