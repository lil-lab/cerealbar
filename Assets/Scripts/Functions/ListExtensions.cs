using System.Collections.Generic;

namespace Cyan.Functions
{
    public static class ListExtensions
    {

        static System.Random rnd = new System.Random();

        public static List<object> Shuffle(this List<object> list)
        {
            var shuffleList = new List<object>();
            for (int i = list.Count - 1; i > 0; i--)
            {
                var index = rnd.Next(i);
                shuffleList.Add(list[index]);
                list.RemoveAt(index);
            }

            shuffleList.Add(list[0]);

            return shuffleList;

        }

        public static void Shuffle<T>(T[] array)
        {
            var count = array.Length;
            for (int  i = array.Length -1; i >= 0 ; i--)
            {
                var r = rnd.Next(i);
                T t = array[r]; //generic type is now this random val
                array[r] = array[i];
                array[i] = t;

            }          
        }
        public static void Shuffle<T>(List<T> list)
        {
            var count = list.Count;
            for (int i = list.Count - 1; i >= 0; i--)
            {
                var r = rnd.Next(i);
                T t = list[r]; //generic type is now this random val
                list[r] = list[i];
                list[i] = t;

            }
        }


    }

}
