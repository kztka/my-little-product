using System;
 
public static class StringExtensions
{
    public static String RemoveEnd(this String str, int len)
    {
        if (str.Length < len) {
            return string.Empty;
        }
 
        return str.Remove(str.Length - len);
    }
}